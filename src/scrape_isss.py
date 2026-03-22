"""
Legacy ISSS scraper (simpler HTML extraction).

For updating the knowledge base, prefer `manual_isss_content.py` at the repo root:
same output path `data/raw_docs/isss_content.json`, richer parsing (fragments, PDFs).
"""
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json

class ISSSScraper:
    def __init__(self):
        self.base_url = "https://isss.gsu.edu"
        self.visited = set()
        self.documents = []
    
    def scrape_page(self, url):
        #Scrape a single page
        try:
            #Don't scrape the same page twice
            if url in self.visited:
                return
            
            self.visited.add(url)
            print(f"Scraping: {url}")
            
            #Get page content
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract main content (adjust selectors for ISSS site)
            # You might need to inspect the site to find the right selectors
            content_div = soup.find('div', {'class': 'content'}) or soup.find('main')
            
            if content_div:
                # Get text content
                text = content_div.get_text(separator='\\n', strip=True)
                
                # Save document
                self.documents.append({
                    'url': url,
                    'title': soup.find('title').text if soup.find('title') else 'Untitled',
                    'content': text
                })
                
                print(f"  ✅ Saved {len(text)} characters")
            
            # Be polite - don't overwhelm the server
            time.sleep(1)
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    def scrape_multiple_pages(self, urls):
        #Scrape multiple URLs
        for url in urls:
            self.scrape_page(url)
        
        return self.documents
    
    def save_to_file(self, filename):
        #Save scraped content to file
        import json
        
        os.makedirs('data/raw_docs', exist_ok=True)
        filepath = f'data/raw_docs/{filename}'
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, indent=2, ensure_ascii=False)
        
        print(f"\\n✅ Saved {len(self.documents)} documents to {filepath}")

# Use it
if __name__ == "__main__":
    scraper = ISSSScraper()
    
    # Important ISSS pages (add more as you find them)
    urls = [
        "https://isss.gsu.edu/",
        "https://isss.gsu.edu/current-students/",
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
        "https://www.dropbox.com/scl/fi/2zjz9502ixj61k0s30xle/International-Student-Handbook-072021.pdf?rlkey=d8z5szrwh4xp0ukzgu0egvquu&e=1&st=9ttjhyie&dl=0"

    ]
    
    documents = scraper.scrape_multiple_pages(urls)
    scraper.save_to_file('isss_content.json')
    
    print(f"\\n📊 Stats:")
    print(f"  Pages scraped: {len(documents)}")
    print(f"  Total characters: {sum(len(doc['content']) for doc in documents)}")