import os
import json
import re
from bs4 import BeautifulSoup
from docling.document_converter import DocumentConverter
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

class LASCProcessor:
    def __init__(self, raw_dir="data/raw", processed_dir="data/processed"):
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
        self.metadata_path = os.path.join(raw_dir, "metadata.json")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=300,
            separators=["\n# ", "\n## ", "\n### ", "\n\n", "|", "\n", ".", " ", ""]
        )
        self.doc_converter = DocumentConverter()
        os.makedirs(processed_dir, exist_ok=True)

    def clean_text(self, text):
        # 1. Normalize unicode ligatures
        text = text.replace('\ufb01', 'fi').replace('\ufb02', 'fl')
        text = text.replace('\u2013', '-').replace('\u2014', '-')
        text = text.replace('\u2018', "'").replace('\u2019', "'")
        text = text.replace('\u201c', '"').replace('\u201d', '"')

        # 2. Fix fragmented words caused by PDF encoding (e.g., "i n n o v a t i o n")
        text = re.sub(r'(\b\w\s){3,}', lambda m: m.group(0).replace(' ', ''), text)

        # 3. Normalize whitespace while preserving table pipes (|)
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        text = re.sub(r'[ \t]{2,}', ' ', text) # Preserve single spaces but clean tabs/extra spaces
        
        # 4. Join lines only if they are not part of a markdown table/list
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                cleaned_lines.append("")
                continue
            
            # If it looks like a table or heading, don't join
            if line.startswith('|') or line.startswith('#') or line.startswith('- '):
                cleaned_lines.append(line)
                continue

            if cleaned_lines and cleaned_lines[-1] and not re.search(r'[.!?:\d|#]$', cleaned_lines[-1]):
                cleaned_lines[-1] += " " + line
            else:
                cleaned_lines.append(line)

        return "\n".join(l for l in cleaned_lines if l.strip())

    def extract_doc_name_from_url(self, url):
        """Try to extract a human-readable document name from the URL or path."""
        # For lasc.space pages
        if 'lasc.space' in url:
            path = url.rstrip('/').split('/')[-1]
            return path.replace('-', ' ').replace('_', ' ').title() if path else 'LASC Homepage'
        return None

    def extract_html_sections(self, filepath, url):
        """Extract HTML content as a list of Documents, one per section/heading."""
        docs = []
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        page_name = self.extract_doc_name_from_url(url) or filepath

        # Try to split by headings for richer context
        headings = soup.find_all(['h1', 'h2', 'h3'])

        if headings:
            for i, heading in enumerate(headings):
                section_title = heading.get_text(strip=True)
                # Collect all sibling content until next heading
                content = section_title + "\n"
                for sibling in heading.find_next_siblings():
                    if sibling.name and sibling.name in ['h1', 'h2', 'h3']:
                        break
                    if hasattr(sibling, 'get_text'):
                        content += sibling.get_text(separator=' ', strip=True) + "\n"

                content = self.clean_text(content)
                if len(content.strip()) < 50:
                    continue

                docs.append(Document(
                    page_content=content,
                    metadata={
                        "source": url,
                        "doc_name": page_name,
                        "section": section_title,
                        "type": "html",
                        "page": None,
                    }
                ))
        else:
            # Fallback: entire page as one doc
            text = self.clean_text(soup.get_text(separator=' '))
            if text.strip():
                docs.append(Document(
                    page_content=text,
                    metadata={
                        "source": url,
                        "doc_name": page_name,
                        "section": None,
                        "type": "html",
                        "page": None,
                    }
                ))

        return docs

    def extract_with_docling(self, filepath, url):
        """Extract document content using Docling for multi-format support and OCR."""
        docs = []
        try:
            print(f"  Converting with Docling: {filepath}")
            result = self.doc_converter.convert(filepath)
            
            # Export to markdown for structured text
            md_content = result.document.export_to_markdown()
            
            # Get document title from docling metadata or filename
            doc_title = None
            if hasattr(result.document, 'name') and result.document.name:
                doc_title = result.document.name
            else:
                doc_title = os.path.basename(filepath).split('.')[0].replace('_', ' ').title()

            # Split by sections if possible, otherwise use the whole content
            # For simplicity in this version, we treat the MD output as one block 
            # and let the text_splitter handle it, or we can try to split by markdown headers.
            
            # Simple header-based split attempt
            sections = re.split(r'\n#+ ', md_content)
            
            for i, section_text in enumerate(sections):
                if not section_text.strip():
                    continue
                
                # Re-add header marker if it was split
                full_text = section_text if i == 0 else f"# {section_text}"
                cleaned = self.clean_text(full_text)
                
                if len(cleaned) < 50:
                    continue
                
                docs.append(Document(
                    page_content=cleaned,
                    metadata={
                        "source": url,
                        "doc_name": doc_title,
                        "section": f"Section {i}" if i > 0 else "Main",
                        "type": "document",
                        "page": None,
                    }
                ))

        except Exception as e:
            print(f"  Error processing with Docling {filepath}: {e}")

        return docs

    def classify_and_tag(self, text, url):
        keywords = [
            "edital", "rules", "regulation", "normas", "competition",
            "guidelines", "manual", "egm", "lgr", "scsm", "rcsm",
            "scoring", "judging", "evaluation", "award", "criteria"
        ]
        content_lower = text.lower()
        url_lower = url.lower()

        found_keywords = [kw for kw in keywords
                          if kw in content_lower or kw in url_lower]

        return {
            "category": "rules_regulations" if found_keywords else "general",
            "priority": len(found_keywords),
            "keywords": found_keywords
        }

    def process(self):
        if not os.path.exists(self.metadata_path):
            print("No metadata found. Run crawler first.")
            return

        with open(self.metadata_path, 'r') as f:
            metadata = json.load(f)

        # Deduplicate by local path (avoid reprocessing duplicates)
        seen_paths = set()
        unique_metadata = []
        for item in metadata:
            if item['local_path'] not in seen_paths:
                seen_paths.add(item['local_path'])
                unique_metadata.append(item)

        all_docs = []

        for item in unique_metadata:
            filepath = item['local_path']
            url = item['url']
            doc_type = item['type']

            if not os.path.exists(filepath):
                continue

            print(f"Processing: {filepath}")

            if doc_type == "html":
                docs = self.extract_html_sections(filepath, url)
            elif doc_type == "pdf":
                docs = self.extract_with_docling(filepath, url)
            else:
                # Try docling for other types too
                docs = self.extract_with_docling(filepath, url)

            # Tag each doc with keywords/category
            for doc in docs:
                tags = self.classify_and_tag(doc.page_content, url)
                doc.metadata['category'] = tags['category']
                doc.metadata['priority'] = tags['priority']
                doc.metadata['keywords'] = ", ".join(tags['keywords'])

            all_docs.extend(docs)

        # Split into chunks while preserving page/section metadata
        all_chunks = []
        for doc in all_docs:
            chunks = self.text_splitter.split_documents([doc])
            all_chunks.extend(chunks)

        # Save chunks
        output_path = os.path.join(self.processed_dir, "chunks.json")
        serialized = [
            {"page_content": c.page_content, "metadata": c.metadata}
            for c in all_chunks
        ]
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serialized, f, indent=4, ensure_ascii=False)

        print(f"Processing finished. Generated {len(all_chunks)} chunks from {len(all_docs)} sections/pages.")
        return all_chunks


if __name__ == "__main__":
    processor = LASCProcessor()
    processor.process()
