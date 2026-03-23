"""
Legacy ISSS scraper (auto-discovers internal links).

Starts from https://isss.gsu.edu and crawls all internal sublinks,
then scrapes their text content.
"""

import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import time
import json


class ISSSScraper:
    def __init__(self):
        self.base_url = "https://isss.gsu.edu"
        self.allowed_domain = "isss.gsu.edu"
        self.visited = set()
        self.documents = []

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; ISSS-Scraper/1.0)"
        })

    def is_internal_link(self, url):
        parsed = urlparse(url)
        return parsed.netloc == self.allowed_domain

    def normalize_url(self, base, href):
        full_url = urljoin(base, href)
        parsed = urlparse(full_url)

        # only http/https
        if parsed.scheme not in ("http", "https"):
            return None

        # only keep internal links from isss.gsu.edu
        if not self.is_internal_link(full_url):
            return None

        # remove fragments like #section
        clean_url = parsed._replace(fragment="").geturl()

        # skip obvious non-html/static files
        lower = clean_url.lower()
        blocked_exts = (
            ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
            ".mp4", ".mp3", ".zip", ".doc", ".docx",
            ".xls", ".xlsx", ".ppt", ".pptx"
        )
        if lower.endswith(blocked_exts):
            return None

        bad_paths = [
            "/search",
            "/directory",
            "/employment/",
            "/travel/",
        ]

        for p in bad_paths:
            if p in clean_url:
                return None
        return clean_url.rstrip("/")
    
    def is_valid_url(self, url):
        bad_paths = [
            "/search",
            "/directory",
        ]

        for p in bad_paths:
            if p in url:
                return False

        fake_paths = [
            "/employment/",
            "/travel/",
            "/employment/cpt/",
            "/employment/opt/",
        ]

        for p in fake_paths:
            if p in url:
                return False

        return True
    def is_good_content(self, text):
        if not text or len(text) < 300:
            return False

        bad_signals = [
            "SORRY, WE'VE CHANGED THE WEBSITE",
            "Main navigation",
            "Skip to content",
            "Search the Site",
        ]

        text_lower = text.lower()

        for b in bad_signals:
            if b.lower() in text_lower:
                return False

        return True
    
    def discover_links(self, start_url=None, max_pages=300):
        if start_url is None:
            start_url = self.base_url

        queue = deque([start_url])
        discovered = []
        seen = set()

        while queue and len(discovered) < max_pages:
            current_url = queue.popleft()

            if current_url in seen:
                continue
            seen.add(current_url)

            try:
                print(f"Discovering: {current_url}")
                response = self.session.get(current_url, timeout=15)
                response.raise_for_status()

                content_type = response.headers.get("Content-Type", "").lower()
                if "html" not in content_type:
                    continue

                discovered.append(current_url)

                soup = BeautifulSoup(response.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    normalized = self.normalize_url(current_url, a["href"])
                    if normalized and normalized not in seen and normalized not in queue:
                        queue.append(normalized)

                time.sleep(0.5)

            except Exception as e:
                print(f"  ❌ Discovery error on {current_url}: {e}")

        return discovered

    def scrape_page(self, url):
        try:
            if url in self.visited:
                return

            self.visited.add(url)
            print(f"Scraping: {url}")

            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "").lower()
            if "html" not in content_type:
                print("  ⚠️ Skipped non-HTML page")
                return

            soup = BeautifulSoup(response.content, "html.parser")

            # remove junk tags
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()

            # try to get main content first
            content_div = (
                soup.find("main")
                or soup.find("div", {"class": "content"})
                or soup.find("article")
                or soup.body
            )

            if content_div:
                text = content_div.get_text(separator="\n", strip=True)

                if not self.is_valid_url(url):
                    print("  ❌ Skipped fake/bad URL")
                    return

                if not self.is_good_content(text):
                    print("  ❌ Skipped low-quality page")
                    return
                self.documents.append({
                    "url": url,
                    "title": soup.title.text.strip() if soup.title else "Untitled",
                    "content": text
                })

                print(f"  ✅ Saved {len(text)} characters")

            time.sleep(0.5)

        except Exception as e:
            print(f"  ❌ Scrape error on {url}: {e}")

    def scrape_multiple_pages(self, urls):
        for url in urls:
            self.scrape_page(url)
        return self.documents

    def save_to_file(self, filename):
        os.makedirs("data/raw_docs", exist_ok=True)
        filepath = f"data/raw_docs/{filename}"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.documents, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Saved {len(self.documents)} documents to {filepath}")


if __name__ == "__main__":
    scraper = ISSSScraper()

    urls = scraper.discover_links(max_pages=300)
    print(f"\nFound {len(urls)} internal ISSS links")

    documents = scraper.scrape_multiple_pages(urls)
    scraper.save_to_file("isss_content.json")

    print(f"\n📊 Stats:")
    print(f"  Pages scraped: {len(documents)}")
    print(f"  Total characters: {sum(len(doc['content']) for doc in documents)}")