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


def phone_lookup(number):
    """Look up information about a phone number using numverify API (free tier).

    Uses the apilayer numverify free endpoint. If no API key is available,
    falls back to a basic validation with ip-api style data.

    Returns a dict with phone number details.
    """
    cleaned = "".join(c for c in number if c.isdigit() or c == "+")
    if not cleaned:
        raise ValueError("Invalid phone number")

    response = requests.get(
        f"http://apilayer.net/api/validate?number={cleaned}",
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code == 200:
        data = response.json()
        if data.get("valid") is not None:
            return data

    return {
        "valid": False,
        "number": cleaned,
        "error": "Could not validate number (API key may be required)",
    }
