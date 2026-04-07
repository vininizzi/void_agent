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

## 🌍 Deploy e Versatilidade (Modo Híbrido)

O Void Agent foi projetado para ser flexível. Você pode rodá-lo localmente ou em nuvem (ex: Streamlit Cloud).

### Opção A: IA Local (Ollama)
Ideal para privacidade e uso de hardware próprio.

#### 1. Configuração de Rede e CORS (Obrigatório)
Para que o site (na nuvem) consiga "conversar" com o seu PC (local), você deve permitir conexões externas:
- **Linux/Mac**:
  ```bash
  OLLAMA_ORIGINS="*" ollama serve
  ```
- **Windows (PowerShell)**:
  ```powershell
  $env:OLLAMA_ORIGINS="*"; ollama serve
  ```

#### 2. Criando o Túnel com Ngrok (Acesso Externo)
Se o seu site estiver hospedado no Streamlit Cloud, ele não consegue ver o seu `localhost`. Use o **Ngrok** para criar um link público:
1. Instale o [Ngrok](https://ngrok.com/).
2. Com o Ollama rodando, execute:
   ```bash
   ngrok http 11434 --host-header="localhost:11434"
   ```
3. O Ngrok gerará um link (ex: `https://abcd-123.ngrok-free.app`).
4. **No Site**: Copie esse link e cole no campo "Endereço do Ollama" na barra lateral do Void Agent.

### Opção B: IA na Nuvem (Groq - Grátis)
Ideal para deploy rápido sem hardware local.
- **Vantagem**: Não exige túneis ou configurações de rede complexas.
- **Como usar**:
  1. Obtenha uma API Key gratuita em [console.groq.com](https://console.groq.com).
  2. Selecione o modo "Groq Cloud" na barra lateral e cole sua chave.
- **Modelos**: `llama3-70b-8192` (Extremamente rápido e preciso).

---
# void_agent
# void_agent
