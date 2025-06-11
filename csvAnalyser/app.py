import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import pandas as pd
from zipfile import ZipFile
import io

# Carregar variáveis de ambiente
load_dotenv()

# Configurar o Gemini
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# Configurar o modelo
model = genai.GenerativeModel('gemini-2.0-flash')

# Função para processar arquivos CSV dentro de um ZIP
def processar_arquivo_zip(arquivo_zip):
    dados_json = {}
    with ZipFile(arquivo_zip) as zip_file:
        for arquivo in zip_file.namelist():
            if arquivo.endswith('.csv'):
                with zip_file.open(arquivo) as csv_file:
                    df = pd.read_csv(csv_file)
                    if len(df) > 1000:
                        df = df.sample(1000)
                    dados_json[arquivo] = df.to_dict(orient='records')
    return dados_json

# Função para gerar resposta baseada nos dados e na pergunta
def gerar_resposta(prompt, dados_contexto):
    instrucao = """
    Você atuará como um analista de dados inteligente.
    Utilize os dados JSON fornecidos para responder perguntas.
    Estruture sua resposta da seguinte forma:
    1. Interpretação da pergunta
    2. Análise dos dados relevantes
    3. Cálculo ou raciocínio aplicado
    4. Resultado final com explicação
    """
    contexto = f"{instrucao}\n\nContexto dos dados: {json.dumps(dados_contexto, ensure_ascii=False)}\n\nPergunta do usuário: {prompt}"
    resposta = model.generate_content(contexto)
    return resposta.text

# Configuração da página Streamlit
st.set_page_config(page_title="Assistente de Análise de Dados", layout="wide")
st.title("Assistente de Análise de Dados")

# Estado da sessão
if 'dados_processados' not in st.session_state:
    st.session_state.dados_processados = None
if 'historico_chat' not in st.session_state:
    st.session_state.historico_chat = []

# Upload de arquivo ZIP
arquivo_zip = st.file_uploader("Faça upload do arquivo ZIP contendo seus arquivos CSV", type=['zip'])

if arquivo_zip is not None and st.session_state.dados_processados is None:
    with st.spinner('Processando arquivos...'):
        st.session_state.dados_processados = processar_arquivo_zip(arquivo_zip)
    st.success('Arquivos processados com sucesso!')

    # Mostrar resumo dos arquivos processados
    st.subheader("Arquivos processados")
    for arquivo, dados in st.session_state.dados_processados.items():
        df = pd.DataFrame(dados)
        tipos = df.dtypes.to_dict()
        st.write(f"Arquivo: {arquivo} - {len(dados)} registros")
        st.json({col: str(tipo) for col, tipo in tipos.items()})

    # Mostrar dados carregados
    with st.expander("Visualizar dados carregados"):
        for nome, dados in st.session_state.dados_processados.items():
            st.write(f"Arquivo: {nome}")
            st.dataframe(pd.DataFrame(dados).head(10))

    # Botão de resumo estatístico
    if st.button("Gerar resumo estatístico"):
        for nome, dados in st.session_state.dados_processados.items():
            df = pd.DataFrame(dados)
            st.write(f"Resumo estatístico de {nome}")
            st.write(df.describe(include='all'))

# Área de chat
if st.session_state.dados_processados is not None:
    st.subheader("Chat com o Assistente")

    # Histórico de mensagens
    for msg in st.session_state.historico_chat:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Entrada do usuário
    prompt = st.chat_input("Digite sua pergunta sobre os dados...")

    if prompt:
        st.session_state.historico_chat.append({"role": "user", "content": prompt})
        with st.chat_message("assistant"):
            with st.spinner('Analisando...'):
                resposta = gerar_resposta(prompt, st.session_state.dados_processados)
                st.write(resposta)
                st.session_state.historico_chat.append({"role": "assistant", "content": resposta})
else:
    st.info("Envie um arquivo ZIP contendo arquivos CSV para iniciar a análise.")

# Sidebar
with st.sidebar:
    st.subheader("Sobre o Assistente")
    st.write("""
    Este assistente pode ajudar você a:
    - Analisar arquivos CSV
    - Identificar padrões nos dados
    - Realizar cálculos estatísticos
    - Responder perguntas sobre os dados com apoio de IA
    """)

    if st.session_state.dados_processados is not None:
        if st.button("Limpar Dados"):
            st.session_state.dados_processados = None
            st.session_state.historico_chat = []
            st.rerun()
