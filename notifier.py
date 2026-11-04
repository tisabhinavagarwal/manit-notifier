"""Check manit.ac.in for new notices and push a phone notification via ntfy."""
import json
import os
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser

PAGE_URL = "https://www.manit.ac.in/notices-circulars"
SEEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seen.json")
NTFY_SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.sh")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "")
DRY_RUN = os.environ.get("DRY_RUN") == "1"
MAX_SEEN = 3000


class NoticeParser(HTMLParser):
    """Collect (date, title, url) from <div class="notice-date"> / <div class="notice-text"><a>."""

    def __init__(self):
        super().__init__()
        self.notices = []
        self._date = ""
        self._in_date = False
        self._in_text_div = False
        self._href = None
        self._title = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "") or ""
        if tag == "div" and "notice-date" in cls:
            self._in_date = True
            self._date = ""
        elif tag == "div" and "notice-text" in cls:
            self._in_text_div = True
        elif tag == "a" and self._in_text_div and self._href is None:
            self._href = urllib.parse.urljoin(PAGE_URL, a.get("href", ""))
            self._title = []

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            title = " ".join("".join(self._title).split())
            if title:
                self.notices.append({"date": self._date, "title": title, "url": self._href})
            self._href = None
            self._in_text_div = False
        elif tag == "div":
            self._in_date = False

    def handle_data(self, data):
        if self._in_date:
            self._date += data.strip()
        if self._href is not None:
            self._title.append(data)


def fetch_notices():
    req = urllib.request.Request(PAGE_URL, headers={"User-Agent": "Mozilla/5.0 (notice-notifier)"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    parser = NoticeParser()
    parser.feed(html)
    return parser.notices


def key(n):
    return n["url"] + "|" + n["title"]


def push(notice):
    if DRY_RUN:
        print(f"[dry-run] would notify: {notice['date']} {notice['title']}")
        return
    url = notice["url"].replace(" ", "%20")
    req = urllib.request.Request(
        f"{NTFY_SERVER}/{NTFY_TOPIC}",
        data=notice["title"].encode("utf-8"),
        headers={
            "Title": "New MANIT notice",
            "Click": url,
            "Actions": f"view, Open notice, {url}",
            "Tags": "loudspeaker",
            "Priority": "high",
        },
        method="POST",
    )
    urllib.request.urlopen(req, timeout=30).read()
    print(f"notified: {notice['title']}")


def main():
    if not NTFY_TOPIC and not DRY_RUN:
        sys.exit("NTFY_TOPIC is not set")

    notices = fetch_notices()
    if not notices:
        sys.exit("No notices parsed - page layout may have changed or site is down")

    first_run = not os.path.exists(SEEN_FILE)
    seen = [] if first_run else json.load(open(SEEN_FILE, encoding="utf-8"))
    seen_set = set(seen)

    new = [n for n in notices if key(n) not in seen_set]
    if first_run:
        print(f"First run: recorded {len(new)} existing notices, no notifications sent")
    else:
        # Oldest first so the newest notice ends up on top of the phone's list.
        for n in reversed(new):
            push(n)
        print(f"{len(new)} new notice(s)")

    if new:
        seen = [key(n) for n in new] + seen
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(seen[:MAX_SEEN], f, indent=0, ensure_ascii=False)


if __name__ == "__main__":
    main()
