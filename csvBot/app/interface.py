import streamlit as st
from .file_handler import FileHandler
from .agent import QueryAgent
import os

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

    # Upload de arquivo
    uploaded_file = st.file_uploader("Carregue seu arquivo ZIP contendo CSVs", type=['zip'])

    if uploaded_file:
        with st.spinner("Processando arquivos..."):
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
                    st.error(f"Erro ao processar sua pergunta: {str(e)}")
    
    # Botão para limpar dados
    if st.session_state.files_loaded:
        if st.button("Limpar Dados"):
            st.session_state.file_handler.cleanup()
            st.session_state.files_loaded = False
            st.experimental_rerun()
