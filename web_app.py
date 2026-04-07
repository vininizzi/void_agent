import streamlit as st
import time
import os
from src.agent import LASCAgent
from src.pipeline import LASCPipeline

# --- Page Configuration ---
st.set_page_config(
    page_title="Void Agent - LASC Expert",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling ---
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stChatMessage {
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .source-box {
        background-color: #1e2130;
        border-left: 5px solid #4a90e2;
        padding: 10px;
        border-radius: 5px;
        font-size: 0.9em;
        margin-top: 5px;
    }
    .citation-title {
        color: #4a90e2;
        font-weight: bold;
    }
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
    
    st.subheader("⚙️ Configurações de Modelo")
    st.warning("⚠️ Seu sistema possui **1.3GB de RAM** livres. O modelo **llama3.2** (2.0GB) é o que mais se aproxima da sua capacidade disponível.")
    
    # Updated to strictly use models the user confirmed having
    user_models = ["llama3.2", "qwen3.5", "qwen2.5", "llama3", "codellama:7b"]
    model_option = st.selectbox(
        "Modelo Ollama Local", 
        user_models, 
        index=0,
        help="Llama 3.2 (2GB) é o modelo mais leve da sua lista."
    )
    
    if st.button("🔄 Reinicializar / Trocar Modelo"):
        with st.spinner(f"Carregando {model_option}..."):
            st.session_state.agent = LASCAgent(model_name=model_option)
            st.toast(f"Modelo {model_option} carregado!")
            time.sleep(1)
            st.rerun()

    st.divider()
    st.subheader("📊 Status da Base")
    if os.path.exists("data/vectorstore"):
        st.success("✅ Base Vetorial pronta")
    else:
        st.error("❌ Base Vetorial não encontrada")
    
    st.divider()
    st.subheader("🛠️ Sincronização Única")
    st.write("Clique abaixo para baixar, processar e indexar todos os dados em um único fluxo.")
    
    if st.button("🚀 Iniciar Coleta Completa"):
        with st.status("⏳ Executando Pipeline Unificado...", expanded=True) as status:
            try:
                pipeline = LASCPipeline()
                # Run the unified pipeline with status updates
                pipeline.run_full_sync(
                    max_pages=20, 
                    status_callback=lambda msg: status.update(label=msg, state="running")
                )
                
                status.update(label="✅ Sincronização finalizada com sucesso!", state="complete", expanded=False)
                
                # Reload agent to use new index
                st.session_state.agent = LASCAgent(model_name=model_option)
                st.toast("Base de dados atualizada!", icon="🎉")
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                status.update(label=f"❌ Erro no Pipeline: {e}", state="error")
                st.error(f"Erro: {e}")

# --- Agent Initialization (Late init after potential sidebar changes) ---
if "agent" not in st.session_state:
    with st.spinner("🚀 Inicializando Agente LASC..."):
        try:
            st.session_state.agent = LASCAgent(model_name=model_option)
        except Exception as e:
            st.error(f"Erro: {e}. Certifique-se de que o Ollama está rodando e execute: `ollama pull {model_option}`")
            st.stop()

# --- Main Interface ---
st.title("🛰️ LASC RAG Assistant")
st.markdown("Bem-vindo ao assistente do **Latin American Space Challenge**. Como posso ajudar sua equipe hoje?")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("📚 Fontes Consultadas"):
                for idx, source in enumerate(message["sources"], 1):
                    st.markdown(f"**[{idx}]** {source.replace('📄', '📄 **').replace('—', '** —')}")

# Chat input
if prompt := st.chat_input("Pergunte algo (ex: 'Quais os critérios de inovação?')"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🔍 *Consultando base de documentos...*")
        
        try:
            # Query the agent
            result = st.session_state.agent.ask(prompt)
            full_response = result["answer"]
            sources = result["sources"]
            
            # Display response
            message_placeholder.markdown(full_response)
            
            if sources:
                with st.expander("📚 Fontes Consultadas", expanded=False):
                    for idx, source in enumerate(sources, 1):
                         st.markdown(f"**[{idx}]** {source.replace('📄', '📄 **').replace('—', '** —')}")
            
            # Save assistant message
            st.session_state.messages.append({
                "role": "assistant", 
                "content": full_response,
                "sources": sources
            })
            
        except Exception as e:
            st.error(f"Algo deu errado: {e}")
            st.session_state.messages.append({"role": "assistant", "content": f"Erro: {e}"})
