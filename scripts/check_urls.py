"""One-off: check ISSS/Dropbox URLs in scrapers. Run: python scripts/check_urls.py"""
import re
import sys
from pathlib import Path
from urllib.parse import urldefrag

import requests

ROOT = Path(__file__).resolve().parents[1]


def urls_from_manual() -> list[str]:
    text = (ROOT / "manual_isss_content.py").read_text(encoding="utf-8")
    start = text.find("URLS = [")
    if start == -1:
        return []
    end = text.find("\n]", start)
    block = text[start : end + 1]
    return re.findall(r'"(https?://[^"]+)"', block)


def urls_from_scrape_isss() -> list[str]:
    text = (ROOT / "src" / "scrape_isss.py").read_text(encoding="utf-8")
    # urls = [ ... ]
    m = re.search(r"urls\s*=\s*\[(.*?)\n\s*\]", text, re.DOTALL)
    if not m:
        return []
    return re.findall(r'"(https?://[^"]+)"', m.group(1))


def main() -> None:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
    )

    manual = urls_from_manual()
    scrape = urls_from_scrape_isss()

    print("manual_isss_content.py:", len(manual), "URLs")
    print("src/scrape_isss.py:", len(scrape), "URLs")

    all_urls = list(dict.fromkeys(manual + scrape))  # preserve order, unique

    bad: list[tuple[str, int | str, str]] = []
    for u in all_urls:
        base, _frag = urldefrag(u)
        try:
            r = session.get(base, timeout=25, allow_redirects=True)
            code = r.status_code
            final = r.url[:120]
            # Dropbox often returns 302/200; PDF dl links may 403 to bots — note only
            if "dropbox.com" in base.lower():
                if code >= 400:
                    bad.append((u, code, final))
                continue
            if code >= 400:
                bad.append((u, code, final))
            elif code == 200 and "isss.gsu.edu" in base:
                low = (r.text or "").lower()
                snippet = low[:8000]
                if any(
                    x in snippet
                    for x in (
                        "page not found",
                        "nothing found",
                        "oops! that page can&rsquo;t be found",
                        "error 404",
                    )
                ):
                    bad.append((u, "soft-404", final))
        except Exception as e:
            bad.append((u, str(e)[:80], ""))

    print("\n--- FAILED or SUSPICIOUS ---")
    for item in bad:
        print(item[0])
        print("  ->", item[1], item[2])

    if not bad:
        print("(none)")

    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
