import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import zipfile
from dotenv import load_dotenv
from typing import Dict, List
import json

# Carrega variáveis de ambiente
load_dotenv()

# Configura o Gemini AI
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
modelo = genai.GenerativeModel('gemini-2.0-flash')

class AnalisadorInteligente:
    def __init__(self):
        self.dataframes: Dict[str, pd.DataFrame] = {}
        self.contexto_atual = ""
        
    def processar_zip(self, arquivo_zip) -> List[str]:
        """
        Processa o arquivo ZIP e extrai os CSVs
        """
        try:
            with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
                arquivos_csv = [f for f in zip_ref.namelist() if f.lower().endswith('.csv')]
                
                for arquivo in arquivos_csv:
                    with zip_ref.open(arquivo) as csv_file:
                        try:
                            df = pd.read_csv(csv_file)
                            self.dataframes[arquivo] = df
                            st.success(f"✅ Arquivo {arquivo} carregado com sucesso!")
                        except Exception as e:
                            st.error(f"❌ Erro ao carregar {arquivo}: {str(e)}")
                
                return arquivos_csv
        except Exception as e:
            st.error(f"❌ Erro ao abrir o arquivo ZIP: {str(e)}")
            return []

    def identificar_intencao(self, texto: str) -> dict:
        """
        Usa o Gemini para identificar a intenção do usuário
        """
        prompt = f"""
        Analise o texto do usuário e identifique a intenção principal.
        
        Texto: "{texto}"
        
        Arquivos disponíveis: {list(self.dataframes.keys())}
        
        Retorne um JSON com:
        1. "intencao": ["analise_geral", "tendencias", "correlacao", "estatisticas", "comparacao"]
        2. "arquivo": nome do arquivo mencionado ou "todos"
        3. "colunas": lista de colunas mencionadas ou []
        4. "detalhes": detalhes específicos da análise
        
        Responda apenas com o JSON, sem explicações.
        """
        
        try:
            resposta = modelo.generate_content(prompt)
            return json.loads(resposta.text)
        except:
            return {
                "intencao": "analise_geral",
                "arquivo": "todos",
                "colunas": [],
                "detalhes": texto
            }

    def analisar_dados(self, texto: str) -> str:
        """
        Analisa os dados com base na intenção identificada
        """
        intencao = self.identificar_intencao(texto)
        
        # Prepara o contexto para análise
        if intencao["arquivo"] == "todos":
            dfs_info = []
            for nome, df in self.dataframes.items():
                info = f"""
                Arquivo: {nome}
                Linhas: {len(df)}
                Colunas: {', '.join(df.columns)}
                Amostra:
                {df.head(3).to_string()}
                """
                dfs_info.append(info)
            contexto = "\n".join(dfs_info)
        else:
            df = self.dataframes.get(intencao["arquivo"])
            if df is not None:
                contexto = f"""
                Arquivo: {intencao["arquivo"]}
                Linhas: {len(df)}
                Colunas: {', '.join(df.columns)}
                Amostra:
                {df.head().to_string()}
                
                Estatísticas:
                {df.describe().to_string()}
                """
        
        prompt = f"""
        Você é um analista de dados especializado. Analise os dados e responda à pergunta.
        
        REGRAS IMPORTANTES:
        1. Seja EXTREMAMENTE conciso
        2. Responda em no máximo 3 linhas
        3. Liste apenas os dados solicitados
        4. NÃO faça introduções ou conclusões
        5. NÃO dê recomendações ou insights
        6. NÃO mencione análises futuras
        7. Se a pergunta pedir números específicos, liste-os diretamente
        8. Use linguagem simples e direta
        
        Dados:
        {contexto}
        
        Pergunta: {texto}
        
        Responda de forma direta e objetiva, sem explicações adicionais.
        """
        
        try:
            resposta = modelo.generate_content(prompt)
            return resposta.text
        except Exception as e:
            return f"Erro na análise: {str(e)}"

# Configuração da página
st.set_page_config(
    page_title="Analisador Inteligente de CSV",
    page_icon="📊",
    layout="wide"
)

# Inicialização do estado da sessão
if 'analisador' not in st.session_state:
    st.session_state['analisador'] = AnalisadorInteligente()

# Título
st.title("📊 Analisador Inteligente de CSV")

# Área para upload do arquivo
with st.expander("📁 Upload de Arquivo ZIP", expanded=True):
    arquivo_zip = st.file_uploader(
        "Arraste ou selecione um arquivo ZIP contendo CSVs",
        type=['zip'],
        help="O arquivo deve conter um ou mais arquivos CSV"
    )
    
    if arquivo_zip:
        arquivos = st.session_state['analisador'].processar_zip(arquivo_zip)
        if arquivos:
            st.success(f"📊 {len(arquivos)} arquivos CSV encontrados!")

# Área de chat/análise
st.markdown("### 💬 Faça suas perguntas sobre os dados")

if not st.session_state['analisador'].dataframes:
    st.info("⚠️ Primeiro faça o upload de um arquivo ZIP com seus CSVs!")
else:
    st.markdown("""
    Exemplos de perguntas:
    - Me mostre um resumo geral dos dados
    - Quais são as principais tendências?
    - Existe correlação entre as colunas do arquivo X?
    - Qual a média da coluna Y no arquivo Z?
    """)
    
    # Campo de pergunta
    pergunta = st.text_area("Digite sua pergunta:", height=100)
    
    if st.button("📝 Analisar", type="primary"):
        if pergunta:
            with st.spinner("🤔 Analisando os dados..."):
                resposta = st.session_state['analisador'].analisar_dados(pergunta)
                st.markdown("### 📊 Análise")
                st.markdown(resposta)
        else:
            st.warning("⚠️ Por favor, digite uma pergunta!") 