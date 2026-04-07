import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json
import re

class LASCCrawler:
    def __init__(self, base_url="https://www.lasc.space/2026-lasc/documentation", output_dir="data/raw"):
        self.base_url = base_url
        parsed_base = urlparse(base_url)
        self.domain = parsed_base.netloc
        self.base_path = parsed_base.path
        self.output_dir = output_dir
        self.html_dir = os.path.join(output_dir, "html")
        self.pdf_dir = os.path.join(output_dir, "pdf")
        self.metadata_path = os.path.join(output_dir, "metadata.json")
        self.visited_urls = set()
        self.metadata = []
        
        # Load existing metadata for incremental crawling
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'r') as f:
                    self.metadata = json.load(f)
                    for item in self.metadata:
                        self.visited_urls.add(item['url'])
                print(f"Loaded existing metadata: {len(self.metadata)} files already tracked.")
            except Exception as e:
                print(f"Error loading metadata: {e}")

        self.to_visit = [base_url]
        
        # Create directories
        os.makedirs(self.html_dir, exist_ok=True)
        os.makedirs(self.pdf_dir, exist_ok=True)

    def is_valid_url(self, url):
        parsed = urlparse(url)
        # Stay on the same domain and under the /2026-lasc/ path to avoid crawling the whole site
        return parsed.netloc == self.domain and "/2026-lasc/" in parsed.path and url not in self.visited_urls

    def get_google_drive_download_url(self, url):
        # Convert https://drive.google.com/file/d/[FILE_ID]/view to https://drive.google.com/uc?id=[FILE_ID]&export=download
        match = re.search(r'drive\.google\.com/file/d/([^/]+)', url)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/uc?id={file_id}&export=download"
        return None

    def download_pdf(self, url, filename, force=False):
        filepath = os.path.join(self.pdf_dir, filename)
        if not force and os.path.exists(filepath):
            print(f"Skipping PDF (already exists): {filename}")
            return filepath
            
        drive_url = self.get_google_drive_download_url(url)
        download_url = drive_url if drive_url else url
        
        try:
            print(f"Downloading PDF: {url}")
            response = requests.get(download_url, stream=True, timeout=15)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                return filepath
        except Exception as e:
            print(f"Error downloading PDF {url}: {e}")
        return None

    def crawl(self, max_pages=50, force=False):
        count = 0
        if force:
            self.visited_urls = set()
            self.metadata = []
            
        while self.to_visit and count < max_pages:
            url = self.to_visit.pop(0)
            if not force and url in self.visited_urls:
                continue
            
            print(f"Crawling: {url}")
            try:
                response = requests.get(url, timeout=10)
                if response.status_code != 200:
                    continue
                
                self.visited_urls.add(url)
                count += 1
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Save HTML
                filename = urlparse(url).path.strip('/').replace('/', '_') or "index"
                filename += ".html"
                html_path = os.path.join(self.html_dir, filename)
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                self.metadata.append({
                    "url": url,
                    "type": "html",
                    "local_path": html_path
                })
                # Find links
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    full_url = urljoin(url, href)
                    
                    # Check for document links (PDF, DOCX, etc.) or Google Drive links
                    doc_extensions = ('.pdf', '.docx', '.pptx', '.xlsx')
                    is_doc = any(full_url.lower().endswith(ext) for ext in doc_extensions)
                    
                    if is_doc or 'drive.google.com' in full_url:
                        if full_url not in [m['url'] for m in self.metadata]:
                           pdf_filename = full_url.split('/')[-1]
                           if not pdf_filename.endswith('.pdf'):
                                # Try to get ID from drive link for filename
                                match = re.search(r'd/([^/]+)', full_url)
                                if match:
                                    pdf_filename = f"drive_{match.group(1)}.pdf"
                                else:
                                    pdf_filename = f"doc_{len(self.metadata)}.pdf"
                           
                           pdf_path = self.download_pdf(full_url, pdf_filename, force=force)
                           if pdf_path:
                               # Check if already in metadata to avoid duplicates
                               if not any(m['url'] == full_url for m in self.metadata):
                                   self.metadata.append({
                                       "url": full_url,
                                       "type": "pdf",
                                       "local_path": pdf_path
                                   })
                    elif self.is_valid_url(full_url):
                        self.to_visit.append(full_url)
                
                time.sleep(1) # Respectful delay
                
            except Exception as e:
                print(f"Error crawling {url}: {e}")

        # Save metadata
        with open(os.path.join(self.output_dir, "metadata.json"), 'w') as f:
            json.dump(self.metadata, f, indent=4)
        
        print(f"Crawling finished. Visited {count} pages.")

if __name__ == "__main__":
    crawler = LASCCrawler()
    crawler.crawl(max_pages=20) # Limit for first run
