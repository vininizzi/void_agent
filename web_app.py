import streamlit as st
import time
import os
from src.agent import LASCAgent
from src.pipeline import LASCPipeline

# --- Page Configuration ---
st.set_page_config(
    page_title="Void Agent - LASC Expert",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling ---
st.markdown("""
    <style>
    .stChatMessage { border-radius: 10px; padding: 10px; margin-bottom: 10px; }
    .stAlert { border-radius: 10px; }
    .sidebar-section { background-color: #1e2130; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- State Management ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sidebar ---
with st.sidebar:
    st.title("🌌 Void Agent")
    st.caption("Especialista em Regras e Editais LASC")
    st.divider()
    
    st.subheader("🤖 Configuração do Motor de IA")
    ai_mode = st.radio(
        "Selecione o modo de processamento:",
        ["Ollama (Local/Híbrido)", "Groq Cloud (Online Grátis)"],
        index=0,
        help="O modo Ollama usa o seu computador. O modo Groq usa a nuvem."
    )
    
    # --- Ollama Config ---
    if ai_mode == "Ollama (Local/Híbrido)":
        ollama_url = st.text_input("Endereço do Ollama", value="http://localhost:11434").strip()
        
        # Deployment Warning for Localhost
        if "localhost" in ollama_url and "streamlit.app" in st.get_option("browser.serverAddress"):
            st.warning("⚠️ **Dica de Deploy**: Você está na nuvem tentando acessar 'localhost'. Mude o endereço acima para o seu link do **Ngrok**.")

        user_models = ["llama3.2", "qwen3.5", "qwen2.5", "llama3", "codellama:7b"]
        model_option = st.selectbox("Modelo Local", user_models, index=0)
        
        with st.expander("ℹ️ Como configurar p/ rede"):
            st.markdown("""
            Para usar o Ollama do seu PC no site (CORS):
            1. No terminal do seu PC, rode:
               `OLLAMA_ORIGINS="*" ollama serve`
            2. Se estiver fora de casa, use um IP público ou túnel (como ngrok).
            """)
        
        if st.button("🔌 Conectar Ollama"):
            with st.spinner("Conectando..."):
                try:
                    st.session_state.agent = LASCAgent(
                        provider="ollama", 
                        model_name=model_option, 
                        base_url=ollama_url
                    )
                    st.toast("Conectado ao Ollama!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Falha de Conexão: Certifique-se de que o Ollama está rodando e o OLLAMA_ORIGINS está configurado.")

    # --- Groq Config ---
    else:
        groq_key = st.text_input("Groq API Key", type="password", help="Obtenha grátis em console.groq.com")
        st.markdown("[🔗 Pegar chave gratuita no Groq](https://console.groq.com/keys)")
        
        groq_models = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]
        model_option = st.selectbox("Modelo Nuvem", groq_models, index=0)

        if st.button("☁️ Conectar Groq"):
            if not groq_key:
                st.error("Por favor, insira a API Key do Groq.")
            else:
                with st.spinner("Inicializando motor Cloud..."):
                    st.session_state.agent = LASCAgent(
                        provider="groq", 
                        model_name=model_option, 
                        api_key=groq_key
                    )
                    st.toast("Motor Groq Cloud Ativo!")
                    st.rerun()

    st.divider()
    st.subheader("📊 Status da Base")
    if os.path.exists("data/vectorstore"):
        st.success("✅ Documentos Indexados")
    else:
        st.error("❌ Documentos não encontrados")
    
    st.divider()
    st.subheader("🛠️ Sincronização de Dados")
    if st.button("🚀 Iniciar Coleta Completa"):
        with st.status("⏳ Executando Sincronização...", expanded=True) as status:
            try:
                pipeline = LASCPipeline()
                pipeline.run_full_sync(
                    max_pages=20, 
                    status_callback=lambda msg: status.update(label=msg, state="running")
                )
                status.update(label="✅ Sincronização finalizada!", state="complete", expanded=False)
                st.toast("Base de dados atualizada!", icon="🎉")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                status.update(label=f"❌ Erro: {e}", state="error")
                st.error(f"Erro: {e}")

# --- Agent Initialization ---
if "agent" not in st.session_state:
    st.info("👋 Por favor, configure o motor de IA na barra lateral para começar.")
    st.stop()

# --- Main Interface ---
st.title("🛰️ LASC RAG Assistant")
st.markdown("Bem-vindo ao assistente do **Latin American Space Challenge**. Peça detalhes técnicos, regras ou pontuações.")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("📚 Fontes Consultadas"):
                for idx, source in enumerate(message["sources"], 1):
                    st.markdown(f"**[{idx}]** {source.replace('📄', '📄 **').replace('—', '** —')}")

# Chat input
if prompt := st.chat_input("Pergunte algo técnico (ex: 'requisitos de massa do Cansat')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🔍 *Consultando base de documentos...*")
        
        try:
            result = st.session_state.agent.ask(prompt)
            full_response = result["answer"]
            sources = result["sources"]
            
            message_placeholder.markdown(full_response)
            
            if sources:
                with st.expander("📚 Fontes Consultadas", expanded=False):
                    for idx, source in enumerate(sources, 1):
                         st.markdown(f"**[{idx}]** {source.replace('📄', '📄 **').replace('—', '** —')}")
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": full_response,
                "sources": sources
            })
            
        except Exception as e:
            st.error(f"Erro no processamento: {e}")
            st.session_state.messages.append({"role": "assistant", "content": f"Erro: {e}"})
