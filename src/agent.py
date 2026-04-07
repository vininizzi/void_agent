import os
from langchain_community.llms import Ollama
from langchain_groq import ChatGroq
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from .vectorstore import LASCVectorStore

class LASCAgent:
    def __init__(self, provider="ollama", model_name=None, api_key=None, base_url=None):
        """
        Initialize the LASCAgent with a specific provider.
        provider: 'ollama' or 'groq'
        model_name: specific model to use (default based on provider)
        api_key: required for 'groq'
        base_url: custom URL for ollama (useful for network/tunnel)
        """
        self.provider = provider
        self.vs_manager = LASCVectorStore()
        self.vectorstore = self.vs_manager.load_index()
        
        # Determine model name if not provided
        if not model_name:
            self.model_name = "llama3.2" if provider == "ollama" else "llama-3.3-70b-versatile"
        else:
            self.model_name = model_name

        # Setup the LLM based on provider
        if provider == "ollama":
            url = base_url if base_url else "http://localhost:11434"
            self.llm = Ollama(model=self.model_name, base_url=url)
        elif provider == "groq":
            if not api_key:
                raise ValueError("API Key é obrigatória para o modo Online (Groq).")
            self.llm = ChatGroq(
                model_name=self.model_name,
                groq_api_key=api_key
            )
        else:
            raise ValueError(f"Provedor {provider} não suportado.")

        # Strict bilingual prompt
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

            key = f"{source_url}#{page}#{section}"
            if key in seen:
                continue
            seen.add(key)

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
            print(f"\n🔍 Buscando [{self.provider}]: {query}...")
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
            error_str = str(e).lower()
            if "memory" in error_str or "500" in error_str:
                return {
                    "answer": f"❌ Erro de Memória no {self.provider}: O modelo falhou. Se estiver usando Ollama, tente o 'llama3.2' (2GB) ou use o modo Gratuito Online (Groq).",
                    "sources": []
                }
            return {
                "answer": f"❌ Erro na conexão com o motor de IA ({self.provider}): {e}",
                "sources": []
            }

if __name__ == "__main__":
    # Test local
    agent = LASCAgent(provider="ollama")
    print("Agente local inicializado.")
