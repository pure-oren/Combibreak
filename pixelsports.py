import json
import urllib.request
from urllib.error import HTTPError, URLError

# =========================
# CONFIG
# =========================

BASE = "https://pixelsport.tv"
API_EVENTS = f"{BASE}/backend/liveTV/events"
API_SLIDERS = f"{BASE}/backend/slider/getSliders"
OUTPUT_FILE = "Pixelsports.m3u8"

LIVE_TV_LOGO = "https://raw.githubusercontent.com/nero31994/CHANLOGO/refs/heads/main/1762214337176.png"
LIVE_TV_ID = "24.7.Dummy.us"

# Browser-like headers (IMPORTANT)
USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Mobile Safari/537.36"
)

REFERER = "https://pixelsport.tv/"

# =========================
# LEAGUE DATA
# =========================

LEAGUE_INFO = {
    "NFL": ("NFL.Dummy.us", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQp98tY_AU1CnIPb2SbBlRirQMfeQKpIG1yL8UBnyGnXw&s=10", "NFL"),
    "MLB": ("MLB.Baseball.Dummy.us", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSwPbC8Y_P-A2b7KCbbvfHSrkUQcD7SjcKLUbvIx3UIe0XcyRU87xJpcc0G&s=10", "MLB"),
    "NHL": ("NHL.Hockey.Dummy.us", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTyQw9EF5zzC84dCUJcWTLCHw3Xl1mCDdG_sXBF3jFJfGF_2FQ8wa23-Wqq&s=10", "NHL"),
    "NBA": ("NBA.Basketball.Dummy.us", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTPEW4Pqk8--LWwJTrfRkVmKIG0R-_-40I1XGuR4moCIw&s=10", "NBA"),
    "NASCAR": ("Racing.Dummy.us", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR9iyxsyMDVBSKVz6ZEFvbyF6vf-VQFMRQwqVStcN5EjlIXtAV9bO-FI3U&s=10", "NASCAR"),
    "UFC": ("UFC.Fight.Pass.Dummy.us", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSkQfuq2wtbWd0HMVYSyuCS5ODgFJq3pod3wrWFSFjyTQvDP5GtRh8IwJg&s=10", "UFC"),
    "SOCCER": ("Soccer.Dummy.us", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT8NrL5ky4dgtlzSc79brGUkSQtN1NI9SaQuZwuZATiZfC1THi0qrjA7FtC&s=10", "Soccer"),
    "BOXING": ("PPV.EVENTS.Dummy.us", "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSpnIfziDGxqAWn2F_I916ApClUXtsSQUoxWLQaaBZMvQ&s=10", "Boxing"),
}

# =========================
# NETWORK
# =========================

def fetch_json(url):
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": REFERER,
        "Origin": BASE,
        "X-Requested-With": "XMLHttpRequest",
        "Connection": "keep-alive",
    }

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        raise Exception(f"HTTP {e.code} Forbidden")
    except URLError as e:
        raise Exception(f"Network error: {e.reason}")

# =========================
# HELPERS
# =========================

def collect_links(obj, prefix=""):
    links = []
    if not obj:
        return links
    for i in range(1, 4):
        key = f"{prefix}server{i}URL" if prefix else f"server{i}URL"
        url = obj.get(key)
        if url and url.lower() != "null":
            links.append(url)
    return links


def get_league_info(name):
    for key, (tvid, logo, group) in LEAGUE_INFO.items():
        if key.lower() in name.lower():
            return tvid, logo, group
    return ("Pixelsports.Dummy.us", LIVE_TV_LOGO, "Pixelsports")

# =========================
# M3U BUILDER
# =========================

def build_m3u(events, sliders):
    lines = ["#EXTM3U"]

    for ev in events:
        title = ev.get("match_name", "Unknown Event").strip()
        logo = ev.get("competitors1_logo", LIVE_TV_LOGO)
        league = ev.get("channel", {}).get("TVCategory", {}).get("name", "Sports")
        tvid, _, group_display = get_league_info(league)

        links = collect_links(ev.get("channel", {}))
        if not links:
            continue

        for link in links:
            lines.extend([
                f'#EXTINF:-1 tvg-id="{tvid}" tvg-logo="{logo}" group-title="NxB-sports - {group_display}",{title}',
                f"#EXTVLCOPT:http-user-agent={USER_AGENT}",
                f"#EXTVLCOPT:http-referrer={REFERER}",
                link
            ])

    for ch in sliders:
        title = ch.get("title", "Live Channel").strip()
        links = collect_links(ch.get("liveTV", {}))
        if not links:
            continue

        for link in links:
            lines.extend([
                f'#EXTINF:-1 tvg-id="{LIVE_TV_ID}" tvg-logo="{LIVE_TV_LOGO}" group-title="NxB-sports - Live TV",{title}',
                f"#EXTVLCOPT:http-user-agent={USER_AGENT}",
                f"#EXTVLCOPT:http-referrer={REFERER}",
                link
            ])

    return "\n".join(lines)

# =========================
# MAIN
# =========================

def main():
    try:
        print("[*] Fetching PixelSport data...")
        events_data = fetch_json(API_EVENTS)
        sliders_data = fetch_json(API_SLIDERS)

        events = events_data.get("events", [])
        sliders = sliders_data.get("data", [])

        playlist = build_m3u(events, sliders)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(playlist)

        print(f"[+] Saved {OUTPUT_FILE} ({len(events)} events + {len(sliders)} live channels)")
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    main()
