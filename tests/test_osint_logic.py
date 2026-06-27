import socket
from unittest import mock

import pytest
import requests

from osint_logic import (
    _detect_country,
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


# ---- _detect_country ---- #


class TestDetectCountry:
    def test_detects_brazil(self):
        country, prefix = _detect_country("+5511999998888")
        assert country == "BR"
        assert prefix == "+55"

    def test_detects_us(self):
        country, prefix = _detect_country("+14158586273")
        assert country == "US/CA"
        assert prefix == "+1"

    def test_detects_portugal(self):
        country, prefix = _detect_country("+351912345678")
        assert country == "PT"
        assert prefix == "+351"

    def test_returns_none_for_unknown_prefix(self):
        country, prefix = _detect_country("+99912345678")
        assert country is None
        assert prefix is None

    def test_longer_prefix_takes_priority(self):
        country, prefix = _detect_country("+351123456")
        assert prefix == "+351"
        assert country == "PT"


# ---- phone_lookup ---- #


class TestPhoneLookup:
    def _mock_response(self, json_data, status_code=200):
        resp = mock.Mock()
        resp.json.return_value = json_data
        resp.status_code = status_code
        return resp

    def test_brazilian_number_detected(self):
        fake_ip_data = {"country": "Brazil", "query": "1.2.3.4"}
        with mock.patch("osint_logic.requests.get", return_value=self._mock_response(fake_ip_data)):
            result = phone_lookup("+5511999998888")
            assert result["country_code"] == "BR"
            assert result["country_prefix"] == "+55"
            assert result["local_number"] == "11999998888"
            assert result["valid_format"] is True

    def test_us_number_detected(self):
        fake_ip_data = {"country": "United States", "query": "1.2.3.4"}
        with mock.patch("osint_logic.requests.get", return_value=self._mock_response(fake_ip_data)):
            result = phone_lookup("+14158586273")
            assert result["country_code"] == "US/CA"
            assert result["country_prefix"] == "+1"

    def test_number_without_plus_gets_prefixed(self):
        fake_ip_data = {"country": "Brazil", "query": "1.2.3.4"}
        with mock.patch("osint_logic.requests.get", return_value=self._mock_response(fake_ip_data)):
            result = phone_lookup("5511999998888")
            assert result["number"] == "+5511999998888"
            assert result["country_code"] == "BR"

    def test_raises_on_empty_input(self):
        with pytest.raises(ValueError, match="Invalid phone number"):
            phone_lookup("")

    def test_raises_on_non_numeric_input(self):
        with pytest.raises(ValueError, match="Invalid phone number"):
            phone_lookup("abc")

    def test_cleans_number_format(self):
        fake_ip_data = {"country": "Brazil", "query": "1.2.3.4"}
        with mock.patch("osint_logic.requests.get", return_value=self._mock_response(fake_ip_data)):
            result = phone_lookup("+55 (11) 99999-8888")
            assert result["number"] == "+5511999998888"
            assert result["country_code"] == "BR"

    def test_short_number_invalid_format(self):
        fake_ip_data = {"country": "Unknown", "query": "1.2.3.4"}
        with mock.patch("osint_logic.requests.get", return_value=self._mock_response(fake_ip_data)):
            result = phone_lookup("+1234")
            assert result["valid_format"] is False

    def test_unknown_country_prefix(self):
        fake_ip_data = {"country": "Unknown", "query": "1.2.3.4"}
        with mock.patch("osint_logic.requests.get", return_value=self._mock_response(fake_ip_data)):
            result = phone_lookup("+99912345678")
            assert result["country_code"] == "Unknown"
            assert result["country_prefix"] == "Unknown"

    def test_api_failure_still_returns_result(self):
        with mock.patch(
            "osint_logic.requests.get",
            side_effect=requests.ConnectionError("offline"),
        ):
            result = phone_lookup("+5511999998888")
            assert result["country_code"] == "BR"
            assert result["number"] == "+5511999998888"
            assert "lookup_origin_country" not in result

    def test_result_has_required_keys(self):
        fake_ip_data = {"country": "Brazil", "query": "1.2.3.4"}
        with mock.patch("osint_logic.requests.get", return_value=self._mock_response(fake_ip_data)):
            result = phone_lookup("+5511999998888")
            assert "number" in result
            assert "local_number" in result
            assert "country_code" in result
            assert "country_prefix" in result
            assert "valid_format" in result
