import json
import urllib.request
from urllib.error import URLError, HTTPError

BASE = "https://pixelsport.tv"
API_EVENTS = f"{BASE}/backend/liveTV/events"
API_SLIDERS = f"{BASE}/backend/slider/getSliders"
OUTPUT_FILE = "Pixelsports.m3u8"

LIVE_TV_LOGO = "https://raw.githubusercontent.com/nero31994/CHANLOGO/refs/heads/main/1762214337176.png"
LIVE_TV_ID = "24.7.Dummy.us"

VLC_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
VLC_REFERER = f"{BASE}/"
VLC_ICY = "1"

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


def fetch_json(url):
    """Fetch JSON from URL with headers"""
    headers = {
        "User-Agent": VLC_USER_AGENT,
        "Referer": VLC_REFERER,
        "Accept": "*/*",
        "Connection": "close",
        "Icy-MetaData": VLC_ICY,
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def collect_links(obj, prefix=""):
    """Collect valid stream links from object"""
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
    """Return league info tuple: (tvg-id, logo, group name)"""
    for key, (tvid, logo, group) in LEAGUE_INFO.items():
        if key.lower() in name.lower():
            return tvid, logo, group
    return ("Pixelsports.Dummy.us", LIVE_TV_LOGO, "Pixelsports")


def build_m3u(events, sliders):
    """Build the M3U playlist text"""
    lines = ["#EXTM3U"]

    for ev in events:
        title = ev.get("match_name", "Unknown Event").strip()
        logo = ev.get("competitors1_logo", LIVE_TV_LOGO)
        league = ev.get("channel", {}).get("TVCategory", {}).get("name", "Sports")
        tvid, group_logo, group_display = get_league_info(league)
        links = collect_links(ev.get("channel", {}))
        if not links:
            continue

        for link in links:
            lines.append(f'#EXTINF:-1 tvg-id="{tvid}" tvg-logo="{logo}" group-title="NxB-sports - {group_display}",{title}')
            lines.append(f"#EXTVLCOPT:http-user-agent={VLC_USER_AGENT}")
            lines.append(f"#EXTVLCOPT:http-referrer={VLC_REFERER}")
            lines.append(f"#EXTVLCOPT:http-icy-metadata={VLC_ICY}")
            lines.append(link)

    for ch in sliders:
        title = ch.get("title", "Live Channel").strip()
        live = ch.get("liveTV", {})
        logo = LIVE_TV_LOGO  
        links = collect_links(live)
        if not links:
            continue

        for link in links:
            lines.append(f'#EXTINF:-1 tvg-id="{LIVE_TV_ID}" tvg-logo="{logo}" group-title="NxB-sports - Live TV",{title}')
            lines.append(f"#EXTVLCOPT:http-user-agent={VLC_USER_AGENT}")
            lines.append(f"#EXTVLCOPT:http-referrer={VLC_REFERER}")
            lines.append(f"#EXTVLCOPT:http-icy-metadata={VLC_ICY}")
            lines.append(link)

    return "\n".join(lines)


def main():
    try:
        print("[*] Fetching PixelSport data...")
        events_data = fetch_json(API_EVENTS)
        events = events_data.get("events", []) if isinstance(events_data, dict) else []
        sliders_data = fetch_json(API_SLIDERS)
        sliders = sliders_data.get("data", []) if isinstance(sliders_data, dict) else []

        playlist = build_m3u(events, sliders)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(playlist)

        print(f"[+] Saved: {OUTPUT_FILE} ({len(events)} events + {len(sliders)} live channels)")
    except Exception as e:
        print(f"[!] Error: {e}")


if __name__ == "__main__":
    main()
