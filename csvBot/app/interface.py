import streamlit as st
from .file_handler import FileHandler
from .agent import QueryAgent
import os
import logging

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def render_interface():
    st.title("📊 CSVQuery.AI")
    st.write("Faça perguntas sobre seus dados CSV de forma natural!")

    # Inicialização das classes no estado da sessão
    if 'file_handler' not in st.session_state:
        st.session_state.file_handler = FileHandler()
    if 'query_agent' not in st.session_state:
        st.session_state.query_agent = QueryAgent()
    if 'files_loaded' not in st.session_state:
        st.session_state.files_loaded = False
    if 'logs' not in st.session_state:
        st.session_state.logs = []

    # Upload de arquivo
    uploaded_file = st.file_uploader("Carregue seu arquivo ZIP contendo CSVs", type=['zip'])

    if uploaded_file:
        with st.spinner("Processando arquivos..."):
            try:
                # Salvar o arquivo temporariamente
                temp_path = "temp_upload.zip"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getvalue())

                # Processar o arquivo
                success, message = st.session_state.file_handler.process_zip_file(temp_path)
                
                # Limpar arquivo temporário
                if os.path.exists(temp_path):
                    os.remove(temp_path)

                if success:
                    st.success(message)
                    st.session_state.files_loaded = True
                    
                    # Mostrar DataFrames disponíveis
                    st.subheader("DataFrames Carregados:")
                    for df_name in st.session_state.file_handler.get_available_dataframes():
                        st.write(f"- {df_name}")
                else:
                    st.error(message)
                    st.session_state.files_loaded = False
            except Exception as e:
                logger.error(f"Erro ao processar arquivo: {str(e)}")
                st.error(f"Erro ao processar arquivo: {str(e)}")

    # Campo de pergunta
    if st.session_state.files_loaded:
        query = st.text_input("Faça sua pergunta sobre os dados:")
        
        if query:
            with st.spinner("Analisando sua pergunta..."):
                try:
                    # Obter análise do agente
                    analysis = st.session_state.query_agent.analyze_query(
                        query,
                        {name: df for name, df in st.session_state.file_handler.dataframes.items()}
                    )
                    
                    # Executar análise
                    result = st.session_state.query_agent.execute_analysis(
                        analysis,
                        st.session_state.file_handler.dataframes
                    )
                    
                    # Mostrar resultado
                    st.subheader("Resposta:")
                    st.write(result)
                    
                except Exception as e:
                    logger.error(f"Erro ao processar pergunta: {str(e)}")
                    st.error(f"Erro ao processar sua pergunta: {str(e)}")

    # Botão para limpar dados
    if st.session_state.files_loaded:
        if st.button("Limpar Dados"):
            st.session_state.file_handler.cleanup()
            st.session_state.files_loaded = False
            st.rerun()

    # Seção de Debug (expandível)
    with st.expander("🔍 Debug Logs"):
        if st.button("Limpar Logs"):
            st.session_state.logs = []
        
        # Captura os logs do Python
        class StreamlitHandler(logging.Handler):
            def emit(self, record):
                log_entry = self.format(record)
                st.session_state.logs.append(log_entry)

        # Adiciona o handler se ainda não foi adicionado
        if not any(isinstance(h, StreamlitHandler) for h in logger.handlers):
            handler = StreamlitHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)

        # Mostra os logs
        for log in st.session_state.logs[-50:]:  # Mostra apenas os últimos 50 logs
            st.text(log)
