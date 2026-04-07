import os
import json
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

class LASCVectorStore:
    def __init__(self, processed_dir="data/processed", vectorstore_dir="data/vectorstore"):
        self.processed_dir = processed_dir
        self.vectorstore_dir = vectorstore_dir
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.index_name = "lasc_index"
        os.makedirs(vectorstore_dir, exist_ok=True)

    def create_index(self):
        chunks_path = os.path.join(self.processed_dir, "chunks.json")
        if not os.path.exists(chunks_path):
            print("No processed chunks found. Run processor first.")
            return
            
        with open(chunks_path, 'r', encoding='utf-8') as f:
            chunks_data = json.load(f)
            
        documents = [
            Document(page_content=c['page_content'], metadata=c['metadata'])
            for c in chunks_data
        ]
        
        print(f"Indexing {len(documents)} documents...")
        vectorstore = FAISS.from_documents(documents, self.embeddings)
        vectorstore.save_local(self.vectorstore_dir, self.index_name)
        print(f"Vectorstore saved to {self.vectorstore_dir}")
        return vectorstore

    def load_index(self):
        if not os.path.exists(os.path.join(self.vectorstore_dir, f"{self.index_name}.faiss")):
            print("Vectorstore index not found.")
            return None
        return FAISS.load_local(
            self.vectorstore_dir, 
            self.embeddings, 
            self.index_name,
            allow_dangerous_deserialization=True # Local index trust
        )

if __name__ == "__main__":
    vs = LASCVectorStore()
    vs.create_index()
