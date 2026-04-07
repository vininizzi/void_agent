import os
import time
from .crawler import LASCCrawler
from .processor import LASCProcessor
from .vectorstore import LASCVectorStore

class LASCPipeline:
    """Unified pipeline for RAG: Crawl -> Process -> Index."""
    def __init__(self, base_url="https://www.lasc.space/2026-lasc/documentation", 
                 raw_dir="data/raw", processed_dir="data/processed"):
        self.crawler = LASCCrawler(base_url, raw_dir)
        self.processor = LASCProcessor(raw_dir, processed_dir)
        self.vectorstore_manager = LASCVectorStore()

    def run_full_sync(self, max_pages=20, status_callback=None):
        """Runs the entire pipeline in a single flow."""
        try:
            # 0. Cleanup old index (Optional but recommended for version changes)
            if status_callback: status_callback("🧹 Limpando base vetorial antiga...")
            index_path = "data/vectorstore"
            if os.path.exists(index_path):
                import shutil
                shutil.rmtree(index_path)

            # 1. Crawling
            if status_callback: status_callback("🛰️ 1/3: Rastreando o site LASC (Incremental)...")
            self.crawler.crawl(max_pages=max_pages)
            
            # 2. Processing (NLP + PDF extraction with Docling)
            if status_callback: status_callback("📄 2/3: Processando textos e PDFs (NLP/Docling)...")
            self.processor.process()
            
            # 3. Indexing
            if status_callback: status_callback("🧠 3/3: Atualizando Base Vetorial FAISS...")
            self.vectorstore_manager.create_index()
            
            if status_callback: status_callback("✅ Sincronização Completa!")
            return True
        except Exception as e:
            if status_callback: status_callback(f"❌ Erro no Pipeline: {e}")
            raise e

if __name__ == "__main__":
    pipeline = LASCPipeline()
    pipeline.run_full_sync()
