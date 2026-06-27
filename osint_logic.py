import socket
import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}
REQUEST_TIMEOUT = 5

SITES = {
    "GitHub": "https://github.com/{username}",
    "GitLab": "https://gitlab.com/{username}",
    "Bitbucket": "https://bitbucket.org/{username}",
    "Twitter/X": "https://twitter.com/{username}",
    "Instagram": "https://www.instagram.com/{username}",
    "Facebook": "https://www.facebook.com/{username}",
    "Reddit": "https://www.reddit.com/user/{username}",
    "TikTok": "https://www.tiktok.com/@{username}",
    "YouTube": "https://www.youtube.com/@{username}",
    "Medium": "https://medium.com/@{username}",
    "Pinterest": "https://www.pinterest.com/{username}",
    "SoundCloud": "https://soundcloud.com/{username}",
    "Steam": "https://steamcommunity.com/id/{username}",
    "Twitch": "https://www.twitch.tv/{username}",
    "DeviantArt": "https://www.deviantart.com/{username}",
    "HackerOne": "https://hackerone.com/{username}",
    "Keybase": "https://keybase.io/{username}",
    "Flickr": "https://www.flickr.com/people/{username}",
    "About.me": "https://about.me/{username}",
    "Spotify": "https://spotify.com/{username}",
}


def resolve_dns(domain):
    """Resolve a domain name to an IP address."""
    return socket.gethostbyname(domain)


def get_ip_info(ip):
    """Query ip-api.com for information about an IP address."""
    response = requests.get(
        f"http://ip-api.com/json/{ip}",
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def search_username(username):
    """Check if a username exists on various platforms.

    Returns a list of dicts with keys: site, url, status.
    status is one of 'found', 'not_found', 'error'.
    """
    results = []
    for site, url_template in SITES.items():
        url = url_template.format(username=username)
        try:
            r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                status = "found"
            else:
                status = "not_found"
        except requests.RequestException:
            status = "error"
        results.append({"site": site, "url": url, "status": status})
    return results


COUNTRY_CODES = {
    "+1": "US/CA",
    "+55": "BR",
    "+44": "GB",
    "+351": "PT",
    "+34": "ES",
    "+33": "FR",
    "+49": "DE",
    "+39": "IT",
    "+81": "JP",
    "+86": "CN",
    "+91": "IN",
    "+61": "AU",
    "+52": "MX",
    "+54": "AR",
    "+56": "CL",
    "+57": "CO",
    "+58": "VE",
    "+353": "IE",
    "+31": "NL",
    "+46": "SE",
    "+47": "NO",
    "+48": "PL",
    "+7": "RU",
    "+82": "KR",
    "+90": "TR",
    "+20": "EG",
    "+27": "ZA",
    "+234": "NG",
    "+971": "AE",
    "+966": "SA",
}


def _detect_country(number):
    """Detect country from phone number prefix."""
    for prefix in sorted(COUNTRY_CODES, key=len, reverse=True):
        if number.startswith(prefix):
            return COUNTRY_CODES[prefix], prefix
    return None, None


def phone_lookup(number):
    """Look up information about a phone number.

    Validates the number format, detects the country from the prefix,
    and queries a free API for additional info when available.

    Returns a dict with phone number details.
    """
    cleaned = "".join(c for c in number if c.isdigit() or c == "+")
    if not cleaned or not any(c.isdigit() for c in cleaned):
        raise ValueError("Invalid phone number")

    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned

    country, prefix = _detect_country(cleaned)
    local_number = cleaned[len(prefix):] if prefix else cleaned.lstrip("+")

    result = {
        "number": cleaned,
        "local_number": local_number,
        "country_code": country if country else "Unknown",
        "country_prefix": prefix if prefix else "Unknown",
        "valid_format": len(local_number) >= 6,
    }

    try:
        response = requests.get(
            f"http://ip-api.com/json/",
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code == 200:
            data = response.json()
            result["lookup_origin_country"] = data.get("country", "Unknown")
            result["lookup_origin_ip"] = data.get("query", "Unknown")
    except requests.RequestException:
        pass

    return result
