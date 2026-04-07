import argparse
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.pipeline import LASCPipeline
from src.agent import LASCAgent

def main():
    parser = argparse.ArgumentParser(description="Void Agent - Assistente RAG LASC")
    parser.add_argument("--web",       action="store_true", help="Iniciar interface Web Streamlit")
    parser.add_argument("--full",      action="store_true", help="Executar pipeline completo (Crawl -> Process -> Index)")
    parser.add_argument("--chat",      action="store_true", help="Iniciar chat direto no terminal")
    parser.add_argument("--pages",     type=int, default=20,     help="Número máx. de páginas para rastreio (default: 20)")
    parser.add_argument("--model",     type=str, default="llama3.2", help="Modelo Ollama a usar (sugerido: llama3.2 para baixa RAM)")

    args = parser.parse_args()

    # Step 0: Launch Web UI
    if args.web:
        print("\n" + "="*50)
        print("  🛰️ Iniciando Interface Web Streamlit...")
        print("="*50)
        os.system("streamlit run web_app.py")
        return

    # Step 1: Integrated Pipeline
    if args.full:
        print("\n" + "="*50)
        print("  🚀 Iniciando Sincronização Unificada")
        print("="*50)
        pipeline = LASCPipeline()
        pipeline.run_full_sync(max_pages=args.pages, status_callback=print)

    # Step 2: CLI Chat Agent
    if args.chat:
        print("\n" + "="*50)
        print("  LASC AI Agent — Modo CLI")
        print("="*50)

        agent = LASCAgent(model_name=args.model)

        print(f"\n✅ Agente pronto! Modelo: {args.model}")
        print("💬 Pergunte qualquer coisa sobre as regras do LASC. Digite 'sair' para encerrar.\n")

        while True:
            try:
                query = input("Você: ").strip()
                if not query: continue
                if query.lower() in ['sair', 'exit', 'quit']: break

                result = agent.ask(query)
                print(f"\n{'-'*50}\n🤖 Agente:\n{result['answer']}")

                if result.get('sources'):
                    print(f"\n📚 Fontes Consultadas:")
                    for idx, cit in enumerate(result['sources'], 1):
                        lines = cit.split('\n')
                        print(f"  [{idx}] {lines[0]}")
                        for extra in lines[1:]: print(f"       {extra}")
                print(f"{'-'*50}\n")

            except (KeyboardInterrupt, EOFError):
                print("\nEncerrando...")
                break
            except Exception as e:
                print(f"\n❌ Erro: {e}")

if __name__ == "__main__":
    main()
