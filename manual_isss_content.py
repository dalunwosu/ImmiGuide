import json
import os
import re
from typing import Any
from urllib.parse import urldefrag

import requests
from bs4 import BeautifulSoup, Tag

try:
    from pypdf import PdfReader  # type: ignore
except Exception:
    PdfReader = None

# Page list for ISSS scraping. Re-verify after edits: `python scripts/check_urls.py`
URLS = [
    "https://isss.gsu.edu/",
    "https://isss.gsu.edu/directory/",
    "https://isss.gsu.edu/directory/#atlanta-campus-isss-staff",
    "https://isss.gsu.edu/directory/#perimeter-campuses-isss-staff",
    "https://isss.gsu.edu/directory/#isss-student-staff",
    "https://isss.gsu.edu/about/policies/",
    "https://isss.gsu.edu/about/policies/#certificate-programs",
    "https://isss.gsu.edu/about/policies/#change-of-status",
    "https://isss.gsu.edu/about/policies/#completion-of-study",
    "https://isss.gsu.edu/about/policies/#concurrent-enrollment",
    "https://isss.gsu.edu/about/policies/#curricular-practical-training",
    "https://isss.gsu.edu/about/policies/#extension-of-f-1-program",
    "https://isss.gsu.edu/about/policies/#extension-of-j-1-program",
    "https://isss.gsu.edu/about/policies/#f-1-change-of-level",
    "https://isss.gsu.edu/about/policies/#f-2-enrollment",
    "https://isss.gsu.edu/about/policies/#i-20-issuance-deadlines-for-new-students",
    "https://isss.gsu.edu/about/policies/#j-1-academic-training",
    "https://isss.gsu.edu/about/policies/#optional-practical-training",
    "https://isss.gsu.edu/about/policies/#optional-practical-training-stem-extension",
    "https://isss.gsu.edu/about/policies/#post-baccalaureate-study",
    "https://isss.gsu.edu/about/policies/#recruiters-and-international-recruits",
    "https://isss.gsu.edu/about/policies/#reduced-course-load-academic-reasons",
    "https://isss.gsu.edu/about/policies/#reduced-course-load-medical-reasons",
    "https://isss.gsu.edu/about/policies/#reduced-course-load-pregnancy",
    "https://isss.gsu.edu/about/policies/#study-abroad",
    "https://isss.gsu.edu/about/policies/#transfer",
    "https://isss.gsu.edu/about/international-enrollment-statistics/",
    "https://www.dropbox.com/scl/fi/8gubqvnph0k6934upciqr/OpenDoors_FactSheet_Georgia_-2025.pdf?rlkey=ue6mhobndsrfwxi27i06mstnk&e=1&st=1xr7mopi&dl=1",
    "https://isss.gsu.edu/about/international-families/",
    "https://isss.gsu.edu/incoming-students/step-1-admissions/",
    "https://isss.gsu.edu/incoming-students/step-1-admissions/sevis-student-exchange-visitor-information-system/",
    "https://isss.gsu.edu/incoming-students/step-1-admissions/f1-students-request-form-i20/",
    "https://isss.gsu.edu/incoming-students/step-1-admissions/f1-students-request-form-i20/#copy-of-your-passport-identification-page",
    "https://isss.gsu.edu/incoming-students/step-1-admissions/f1-students-request-form-i20/#financial-documentation",
    "https://isss.gsu.edu/incoming-students/step-1-admissions/learn-about-istart/",
    "https://isss.gsu.edu/incoming-students/step-1-admissions/j-1-exchange-students/",
    "https://isss.gsu.edu/incoming-students/step-1-admissions/fulbright-muskie-and-externally-sponsored-students/",
    "https://isss.gsu.edu/incoming-students/step-1-admissions/transfer-to-georgia-state/",
    "https://isss.gsu.edu/incoming-students/step-1-admissions/review-estimated-costs-of-attendance/",
    "https://isss.gsu.edu/incoming-students/step-1-admissions/faq-international-admissions/",
    "https://isss.gsu.edu/incoming-students/step-1-admissions/next-steps-atlanta-campus/",
    "https://isss.gsu.edu/incoming-students/step-1-admissions/next-steps-perimeter-college/",
    "https://isss.gsu.edu/incoming-students/step-2-pre-arrival/",
    "https://isss.gsu.edu/incoming-students/step-2-pre-arrival/helpful-information/#video-sevis-immigration-documents-visas-and-us-port-of-entry",
    "https://isss.gsu.edu/incoming-students/step-2-pre-arrival/helpful-information/#when-to-arrive-airport-and-baggage-port-of-entry-process-secondary-inspection",
    "https://isss.gsu.edu/incoming-students/step-2-pre-arrival/helpful-information/#housing-and-dining-options-campus-shuttle-other-things-to-consider",
    "https://isss.gsu.edu/incoming-students/step-2-pre-arrival/helpful-information/#campus-police-safety-tips-emergency-phone-numbers",
    "https://isss.gsu.edu/incoming-students/step-2-pre-arrival/helpful-information/#georgia-state-health-clinic-and-services",
    "https://isss.gsu.edu/incoming-students/step-2-pre-arrival/helpful-information/#understanding-overall-emotional-psychological-and-lifestyle-well-being",
    "https://isss.gsu.edu/incoming-students/step-2-pre-arrival/helpful-information/#video-understanding-what-sexual-misconduct-means-in-the-us",
    "https://isss.gsu.edu/incoming-students/step-2-pre-arrival/apply-for-your-visa/",
    "https://isss.gsu.edu/incoming-students/step-2-pre-arrival/review-international-student-handbook/",
    "https://isss.gsu.edu/incoming-students/step-2-pre-arrival/connect-with-isss/",
    "https://isss.gsu.edu/incoming-students/step-2-pre-arrival/review-housing-options-meal-plans/",
    "https://isss.gsu.edu/incoming-students/step-2-pre-arrival/review-housing-options-meal-plans/#university-housing",
    "https://isss.gsu.edu/incoming-students/step-2-pre-arrival/review-housing-options-meal-plans/#global-living-learning-community",
    "https://isss.gsu.edu/incoming-students/step-2-pre-arrival/review-housing-options-meal-plans/#on-campus-meal-plans",
    "https://isss.gsu.edu/incoming-students/step-2-pre-arrival/review-housing-options-meal-plans/#resources-and-options",
    "https://isss.gsu.edu/incoming-students/step-2-pre-arrival/plan-your-arrival-date/",
    "https://isss.gsu.edu/incoming-students/step-3-arrival-and-orientation/",
    "https://isss.gsu.edu/incoming-students/step-3-arrival-and-orientation/prepare-for-arrival-in-the-u-s/",
    "https://isss.gsu.edu/incoming-students/step-3-arrival-and-orientation/atl-airport-and-local-transportation/",
    "https://isss.gsu.edu/short-term-hotel-options/",
    "https://isss.gsu.edu/international-check-in-and-orientation/",
    "https://isss.gsu.edu/incoming-students/step-3-arrival-and-orientation/global-grillout/",
    "https://isss.gsu.edu/current-students/campus-community-involvement/visa-leader-program/",
    "https://isss.gsu.edu/placement-tests/",
    "https://isss.gsu.edu/placement-tests/#graduate-students",
    "https://isss.gsu.edu/placement-tests/#undergraduate-students",
    "https://isss.gsu.edu/incoming-students/step-3-arrival-and-orientation/student-health-resources/",

]

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        )
    }
)


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\r", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def extract_title(soup: BeautifulSoup) -> str:
    h1 = soup.find("h1")
    if h1:
        return clean_text(h1.get_text(" ", strip=True))
    if soup.title:
        return clean_text(soup.title.get_text(" ", strip=True))
    return "Untitled"


def extract_main_text(soup: BeautifulSoup) -> str:
    main = soup.find("main") or soup.find("article") or soup.find(class_=re.compile(r"content|entry|page", re.I)) or soup.body
    if not main:
        return ""
    for tag in main.find_all(["script", "style", "noscript", "svg", "img", "iframe", "form"]):
        tag.decompose()
    text = main.get_text("\n", strip=True)
    return clean_text(text)


def section_root_for_fragment(soup: BeautifulSoup, fragment: str) -> Tag | None:
    target = soup.find(id=fragment)
    if not target:
        return None
    if target.name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        return target
    heading = target.find(["h1", "h2", "h3", "h4", "h5", "h6"])
    if isinstance(heading, Tag):
        return heading
    parent_heading = target.find_parent(["h1", "h2", "h3", "h4", "h5", "h6"])
    if isinstance(parent_heading, Tag):
        return parent_heading
    return target if isinstance(target, Tag) else None


def extract_fragment_text(soup: BeautifulSoup, fragment: str) -> str:
    root = section_root_for_fragment(soup, fragment)
    if not root:
        return extract_main_text(soup)

    parts: list[str] = [clean_text(root.get_text(" ", strip=True))]

    if root.name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        current_level = int(root.name[1])
        for sibling in root.next_siblings:
            if isinstance(sibling, Tag):
                if sibling.name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
                    next_level = int(sibling.name[1])
                    if next_level <= current_level:
                        break
                text = clean_text(sibling.get_text("\n", strip=True))
                if text:
                    parts.append(text)
    else:
        text = clean_text(root.get_text("\n", strip=True))
        if text:
            parts = [text]

    return clean_text("\n\n".join(parts))


def extract_pdf_text_from_bytes(data: bytes) -> str:
    if PdfReader is None:
        return "PDF downloaded, but pypdf is not installed so the text was not extracted. Install pypdf to parse PDF content."

    import io

    reader = PdfReader(io.BytesIO(data))
    pages: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages.append(page_text)
    return clean_text("\n\n".join(pages))


def scrape_one(url: str) -> dict[str, Any]:
    base_url, fragment = urldefrag(url.strip())
    response = SESSION.get(base_url, timeout=30)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    is_pdf = "pdf" in content_type.lower() or base_url.lower().endswith(".pdf")

    if is_pdf:
        text = extract_pdf_text_from_bytes(response.content)
        title = os.path.basename(base_url) or "PDF Document"
        return {
            "url": url,
            "base_url": base_url,
            "fragment": fragment or None,
            "title": title,
            "content_type": "application/pdf",
            "content": text,
        }

    soup = BeautifulSoup(response.text, "html.parser")
    title = extract_title(soup)
    content = extract_fragment_text(soup, fragment) if fragment else extract_main_text(soup)

    return {
        "url": url,
        "base_url": base_url,
        "fragment": fragment or None,
        "title": title,
        "content_type": "text/html",
        "content": content,
    }


def scrape_all(urls: list[str]) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for index, url in enumerate(urls, start=1):
        try:
            print(f"[{index}/{len(urls)}] Scraping: {url}")
            documents.append(scrape_one(url))
        except Exception as exc:
            documents.append(
                {
                    "url": url,
                    "base_url": urldefrag(url.strip())[0],
                    "fragment": urldefrag(url.strip())[1] or None,
                    "title": "SCRAPE_FAILED",
                    "content_type": None,
                    "content": "",
                    "error": str(exc),
                }
            )
            print(f"    Failed: {exc}")
    return documents


def deduplicate_documents(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str | None]] = set()
    for doc in documents:
        key = (doc.get("url", ""), doc.get("fragment"))
        if key not in seen:
            seen.add(key)
            unique.append(doc)
    return unique


def save_json(filepath: str, documents: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)

    total_chars = sum(len(doc.get("content", "")) for doc in documents)
    print(f"\nSaved {len(documents)} documents to {filepath}")
    print(f"Total content characters: {total_chars:,}")


if __name__ == "__main__":
    print("=" * 70)
    print("SCRAPING ISSS CONTENT INTO ONE JSON FILE")
    print("=" * 70)

    documents = scrape_all(URLS)
    documents = deduplicate_documents(documents)
    save_json("data/raw_docs/isss_content.json", documents)

    print("\nDone.")
