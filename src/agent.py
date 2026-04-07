from langchain_community.llms import Ollama
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from .vectorstore import LASCVectorStore
import os

class LASCAgent:
    def __init__(self, model_name="llama3.2"):
        self.model_name = model_name
        self.vs_manager = LASCVectorStore()
        self.vectorstore = self.vs_manager.load_index()

        # Setup the local LLM via Ollama
        self.llm = Ollama(model=model_name, base_url="http://localhost:11434")

        # Strict bilingual prompt — instructs the model to use context only
        template = """Você é um assistente técnico especializado no LASC (Latin American Space Challenge).
Baseie suas respostas EXCLUSIVAMENTE nos documentos fornecidos no contexto abaixo.

MISSÃO CRÍTICA:
Extraia e exiba prioritariamente DADOS TÉCNICOS, MEDIDAS NUMÉRICAS, LIMITES E REQUISITOS (ex: kg, mm, m, m/s). 
Se houver tabelas de requisitos no contexto, formate sua resposta como uma TABELA MARKDOWN.

INSTRUÇÕES DETALHADAS:
1. Os documentos estão em INGLÊS. Responda em PORTUGUÊS com alta precisão técnica.
2. Não use resumos genéricos se houver dados brutos disponíveis. No lugar de "o Cansat é leve", diga "o Cansat deve ter massa máxima de X kg".
3. Termos equivalentes: Inovação (Innovation/Novelty), Avaliação (Scoring/Criteria), CanSat (Satellite/Payload).
4. Se encontrar contradições ou limites (ex: "mínimo 3000m, máximo 4000m"), reporte ambos.
5. Se o dado técnico não estiver no contexto, responda: "Não encontrei os dados técnicos específicos para este item nos documentos indexados."

Contexto dos Documentos:
{context}

Pergunta: {question}

Resposta Técnica Detalhada (use tabelas se possível):"""

        self.qa_prompt = PromptTemplate(
            template=template, input_variables=["context", "question"]
        )

    def format_sources(self, source_docs):
        """Format source documents into a rich, readable citation list."""
        seen = set()
        citations = []

        for doc in source_docs:
            meta = doc.metadata
            source_url = meta.get('source', 'URL desconhecida')
            doc_name = meta.get('doc_name', '')
            section = meta.get('section', '')
            page = meta.get('page')
            total_pages = meta.get('total_pages')
            doc_type = meta.get('type', '')

            # Build a unique key to avoid duplicate citations
            key = f"{source_url}#{page}#{section}"
            if key in seen:
                continue
            seen.add(key)

            # Build citation string
            citation = ""
            if doc_name:
                citation += f"📄 {doc_name}"
            else:
                citation += f"🔗 {source_url}"

            if doc_type == 'pdf' and page:
                if total_pages:
                    citation += f" — Página {page}/{total_pages}"
                else:
                    citation += f" — Página {page}"

            if section:
                citation += f"\n   └─ Seção: \"{section}\""

            if doc_name:
                citation += f"\n   └─ URL: {source_url}"

            citations.append(citation)

        return citations

    def ask(self, query):
        if not self.vectorstore:
            return {
                "answer": "Erro: Base vetorial não encontrada. Por favor, execute a sincronização de dados primeiro.",
                "sources": []
            }

        # Bilingual query expansion to improve retrieval
        expanded_query = (
            f"{query} "
            f"(technical data, numerical requirements, limits, mass, weight, dimensions, mm, kg, m, "
            f"apogee, altitude, recovery, parachute, budget, compliance, innovations, "
            f"scoring criteria, judging system, awards, rules, regulation)"
        )

        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 8}),
            return_source_documents=True,
            chain_type_kwargs={"prompt": self.qa_prompt}
        )

        try:
            print(f"\n🔍 Buscando: {query}...")
            result = qa_chain.invoke({"query": expanded_query})
            
            response = result["result"]
            source_docs = result["source_documents"]
            citations = self.format_sources(source_docs)

            return {
                "answer": response,
                "sources": citations,
                "raw_sources": source_docs
            }
        except Exception as e:
            if "memory" in str(e).lower() or "500" in str(e):
                return {
                    "answer": f"❌ Erro de Memória: O modelo '{self.model_name}' falhou. Seu sistema possui apenas 1.3GB de RAM disponíveis, o que é insuficiente para rodar o 'llama3'.\n\nPor favor, tente um modelo mais leve como 'phi3' ou 'gemma:2b'.\n\n**Ação sugerida:** Execute `ollama pull phi3` e reinicie a aplicação.",
                    "sources": []
                }
            raise e

if __name__ == "__main__":
    agent = LASCAgent()
