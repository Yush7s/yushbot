import socket
from unittest import mock

import pytest
import requests

from osint_logic import (
    get_ip_info,
    phone_lookup,
    resolve_dns,
    search_username,
    SITES,
)


# ---- resolve_dns ---- #


class TestResolveDns:
    def test_returns_ip_for_valid_domain(self):
        with mock.patch("osint_logic.socket.gethostbyname", return_value="93.184.216.34"):
            assert resolve_dns("example.com") == "93.184.216.34"

    def test_raises_on_unknown_domain(self):
        with mock.patch(
            "osint_logic.socket.gethostbyname",
            side_effect=socket.gaierror("Name or service not known"),
        ):
            with pytest.raises(socket.gaierror):
                resolve_dns("this-domain-does-not-exist-xyz.invalid")

    def test_returns_loopback_for_localhost(self):
        with mock.patch("osint_logic.socket.gethostbyname", return_value="127.0.0.1"):
            assert resolve_dns("localhost") == "127.0.0.1"


# ---- get_ip_info ---- #


class TestGetIpInfo:
    def _mock_response(self, json_data, status_code=200):
        resp = mock.Mock()
        resp.json.return_value = json_data
        resp.status_code = status_code
        resp.raise_for_status.return_value = None
        return resp

    def test_returns_dict_with_ip_details(self):
        fake_data = {
            "status": "success",
            "country": "United States",
            "city": "San Francisco",
            "isp": "Cloudflare",
        }
        with mock.patch("osint_logic.requests.get", return_value=self._mock_response(fake_data)):
            result = get_ip_info("1.1.1.1")
            assert result["status"] == "success"
            assert result["country"] == "United States"
            assert result["city"] == "San Francisco"

    def test_raises_on_http_error(self):
        resp = mock.Mock()
        resp.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        with mock.patch("osint_logic.requests.get", return_value=resp):
            with pytest.raises(requests.HTTPError):
                get_ip_info("999.999.999.999")

    def test_raises_on_timeout(self):
        with mock.patch(
            "osint_logic.requests.get",
            side_effect=requests.Timeout("Connection timed out"),
        ):
            with pytest.raises(requests.Timeout):
                get_ip_info("1.1.1.1")

    def test_returns_fail_status_for_private_ip(self):
        fake_data = {
            "status": "fail",
            "message": "private range",
            "query": "192.168.1.1",
        }
        with mock.patch("osint_logic.requests.get", return_value=self._mock_response(fake_data)):
            result = get_ip_info("192.168.1.1")
            assert result["status"] == "fail"


# ---- search_username ---- #


class TestSearchUsername:
    def _make_response(self, status_code):
        resp = mock.Mock()
        resp.status_code = status_code
        return resp

    def test_found_on_all_sites(self):
        with mock.patch(
            "osint_logic.requests.get",
            return_value=self._make_response(200),
        ):
            results = search_username("testuser")
            assert len(results) == len(SITES)
            assert all(r["status"] == "found" for r in results)

    def test_not_found_on_all_sites(self):
        with mock.patch(
            "osint_logic.requests.get",
            return_value=self._make_response(404),
        ):
            results = search_username("nonexistent_user_xyz_12345")
            assert all(r["status"] == "not_found" for r in results)

    def test_error_when_request_fails(self):
        with mock.patch(
            "osint_logic.requests.get",
            side_effect=requests.ConnectionError("Connection refused"),
        ):
            results = search_username("testuser")
            assert all(r["status"] == "error" for r in results)

    def test_result_contains_correct_url(self):
        with mock.patch(
            "osint_logic.requests.get",
            return_value=self._make_response(200),
        ):
            results = search_username("octocat")
            github_result = next(r for r in results if r["site"] == "GitHub")
            assert github_result["url"] == "https://github.com/octocat"

    def test_mixed_responses(self):
        responses = iter(
            [self._make_response(200), self._make_response(404)]
            + [self._make_response(200)] * (len(SITES) - 2)
        )
        with mock.patch("osint_logic.requests.get", side_effect=lambda *a, **kw: next(responses)):
            results = search_username("testuser")
            assert results[0]["status"] == "found"
            assert results[1]["status"] == "not_found"

    def test_each_result_has_required_keys(self):
        with mock.patch(
            "osint_logic.requests.get",
            return_value=self._make_response(200),
        ):
            results = search_username("testuser")
            for r in results:
                assert "site" in r
                assert "url" in r
                assert "status" in r


# ---- phone_lookup ---- #


class TestPhoneLookup:
    def _mock_response(self, json_data, status_code=200):
        resp = mock.Mock()
        resp.json.return_value = json_data
        resp.status_code = status_code
        return resp

    def test_valid_number_returns_data(self):
        fake_data = {
            "valid": True,
            "number": "14158586273",
            "local_format": "4158586273",
            "international_format": "+14158586273",
            "country_prefix": "+1",
            "country_code": "US",
            "country_name": "United States of America",
            "location": "Novato",
            "carrier": "AT&T Mobility LLC",
            "line_type": "mobile",
        }
        with mock.patch("osint_logic.requests.get", return_value=self._mock_response(fake_data)):
            result = phone_lookup("+14158586273")
            assert result["valid"] is True
            assert result["country_code"] == "US"
            assert result["carrier"] == "AT&T Mobility LLC"

    def test_invalid_number_returns_invalid(self):
        fake_data = {"valid": False, "number": "123", "error": "invalid"}
        with mock.patch("osint_logic.requests.get", return_value=self._mock_response(fake_data)):
            result = phone_lookup("123")
            assert result["valid"] is False

    def test_raises_on_empty_input(self):
        with pytest.raises(ValueError, match="Invalid phone number"):
            phone_lookup("")

    def test_raises_on_non_numeric_input(self):
        with pytest.raises(ValueError, match="Invalid phone number"):
            phone_lookup("abc")

    def test_cleans_number_format(self):
        fake_data = {"valid": True, "number": "5511999998888"}
        with mock.patch("osint_logic.requests.get", return_value=self._mock_response(fake_data)) as mock_get:
            phone_lookup("+55 (11) 99999-8888")
            call_url = mock_get.call_args[0][0]
            assert "number=+5511999998888" in call_url

    def test_fallback_when_api_returns_no_valid_field(self):
        fake_data = {"error": "API key required"}
        with mock.patch("osint_logic.requests.get", return_value=self._mock_response(fake_data)):
            result = phone_lookup("+5511999998888")
            assert result["valid"] is False
            assert "error" in result

    def test_fallback_on_api_error(self):
        with mock.patch(
            "osint_logic.requests.get",
            return_value=self._mock_response({}, status_code=500),
        ):
            result = phone_lookup("+5511999998888")
            assert result["valid"] is False

    def test_network_timeout_raises(self):
        with mock.patch(
            "osint_logic.requests.get",
            side_effect=requests.Timeout("timed out"),
        ):
            with pytest.raises(requests.Timeout):
                phone_lookup("+14158586273")
