# 🌌 Void Agent - LASC RAG AI Expert

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/framework-LangChain-orange.svg)](https://python.langchain.com/)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-lightgrey.svg)](https://ollama.com/)
[![FAISS](https://img.shields.io/badge/VectorDB-FAISS-green.svg)](https://github.com/facebookresearch/faiss)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red.svg)](https://streamlit.io/)

O **Void Agent** é um assistente de IA especializado nos Editais e Regulamentos do LASC (Latin American Space Challenge). Ele utiliza uma arquitetura **RAG (Retrieval-Augmented Generation)** para fornecer respostas precisas, baseadas em fontes reais e sem alucinações.

---

## 🚀 Novas Funcionalidades (v2.0)

- **🖥️ Interface Web Premium**: Agora com uma interface gráfica rica feita em **Streamlit**, com suporte a chat, histórico e modo escuro.
- **📑 Citações por Página**: O agente agora identifica exatamente em qual **página do PDF** ou **seção do site** a informação foi encontrada.
- **🔄 Crawler Incremental**: O sistema detecta arquivos já baixados e pula duplicatas, permitindo atualizações rápidas da base.
- **🇧🇷 Agente Bilíngue**: Consulta documentos em Inglês e responde em Português com alta fidelidade técnica.

---

## 🕹️ Como Rodar

O projeto utiliza o arquivo `main.py` como ponto de entrada principal.

### 1. Iniciar a Interface Web (Recomendado)
Para uma experiência visual completa com chat e fontes formatadas:
```bash
python main.py --web
```

### 2. Sincronização Incremental
Para buscar novos documentos no site sem baixar tudo do zero novamente:
```bash
python main.py --crawl --pages 50
```

### 3. Modo CLI (Terminal)
Se preferir o terminal clássico:
```bash
python main.py --chat
```

---

## 🏗️ Estrutura do Projeto

| Componente | Descrição |
| :--- | :--- |
| `web_app.py` | Interface gráfica Streamlit. |
| `src/agent.py` | Lógica RAG, prompt bilíngue e formatação de fontes. |
| `src/crawler.py` | Crawler com suporte a atualização incremental. |
| `src/processor.py` | Processamento inteligente de PDFs (página por página). |
| `src/vectorstore.py` | Gerenciamento do banco FAISS. |

---

## 🛠️ Instalação e Uso Automático

1.  **Ativar o Ambiente**:
    ```bash
    conda activate VOID
    ```
2.  **Instalar Dependências**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Certificar o Ollama**:
    Certifique-se de que o **Ollama** está rodando (`ollama serve`) e o modelo baixado:
    ```bash
    ollama pull llama3
    ```
4.  **Iniciar a Interface Web**:
    ```bash
    python main.py --web
    ```

---
*Desenvolvido com ❤️ por Antigravity AI*
# void_agent
# void_agent
