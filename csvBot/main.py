import streamlit as st
from app.interface import render_interface
from dotenv import load_dotenv
import os

def main():
    # Carrega as variáveis de ambiente do arquivo .env
    load_dotenv()
    
    # Verifica se a chave API está configurada
    if not os.getenv('GOOGLE_API_KEY'):
        st.error("⚠️ GOOGLE_API_KEY não encontrada no arquivo .env. Por favor, configure sua chave API.")
        st.stop()
    
    # Configura a página
    st.set_page_config(page_title="CSVQuery.AI", layout="wide")
    render_interface()

if __name__ == "__main__":
    main()
