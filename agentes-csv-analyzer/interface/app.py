import os
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import google.generativeai as genai
import sys
import json

# Adiciona o diretório pai ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.loader_agent import LoaderAgent
from agents.supplier_analysis_agent import SupplierAnalysisAgent
from agents.item_analysis_agent import ItemAnalysisAgent

# Configuração do Gemini
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Inicialização dos agentes
@st.cache_resource
def get_agents():
    return LoaderAgent(), SupplierAnalysisAgent(), ItemAnalysisAgent()

loader, supplier_agent, item_agent = get_agents()

def execute_analysis(query: str, df_cabecalho: pd.DataFrame = None, df_itens: pd.DataFrame = None) -> dict:
    """Executa análises específicas baseadas na pergunta."""
    results = {}
    
    query = query.lower()
    
    try:
        # Análise de fornecedores/valores
        if any(word in query for word in ['fornecedor', 'valor', 'montante', 'recebido']):
            if df_cabecalho is not None and 'RAZÃO SOCIAL EMITENTE' in df_cabecalho.columns:
                # Agrupa por fornecedor e soma os valores
                valores_por_fornecedor = df_cabecalho.groupby('RAZÃO SOCIAL EMITENTE')['VALOR NOTA FISCAL'].sum()
                top_fornecedor = valores_por_fornecedor.sort_values(ascending=False).head(1)
                
                results['top_fornecedor'] = {
                    'nome': top_fornecedor.index[0],
                    'valor_total': float(top_fornecedor.values[0]),
                    'ranking_completo': valores_por_fornecedor.sort_values(ascending=False).head().to_dict()
                }
                
                # Cria gráfico
                df_plot = pd.DataFrame(valores_por_fornecedor.sort_values(ascending=False).head(10))
                fig = px.bar(df_plot, title='Top 10 Fornecedores por Valor Total')
                results['grafico'] = fig

        # Análise de itens/produtos
        if any(word in query for word in ['item', 'produto', 'quantidade']):
            if df_itens is not None:
                # Agrupa por produto e soma as quantidades
                qtd_por_produto = df_itens.groupby('DESCRIÇÃO DO PRODUTO/SERVIÇO')['QUANTIDADE'].sum()
                top_produto = qtd_por_produto.sort_values(ascending=False).head(1)
                
                results['top_produto'] = {
                    'nome': top_produto.index[0],
                    'quantidade_total': float(top_produto.values[0]),
                    'ranking_completo': qtd_por_produto.sort_values(ascending=False).head().to_dict()
                }
                
                # Cria gráfico
                df_plot = pd.DataFrame(qtd_por_produto.sort_values(ascending=False).head(10))
                fig = px.bar(df_plot, title='Top 10 Produtos por Quantidade')
                results['grafico'] = fig

        # Análise temporal
        if any(word in query for word in ['quando', 'data', 'período', 'tempo']):
            if df_cabecalho is not None and 'DATA EMISSÃO' in df_cabecalho.columns:
                df_cabecalho['DATA'] = pd.to_datetime(df_cabecalho['DATA EMISSÃO'])
                valores_por_dia = df_cabecalho.groupby('DATA')['VALOR NOTA FISCAL'].sum()
                
                results['analise_temporal'] = {
                    'dia_maior_valor': valores_por_dia.idxmax().strftime('%Y-%m-%d'),
                    'valor_maximo': float(valores_por_dia.max()),
                    'media_diaria': float(valores_por_dia.mean())
                }
                
                # Cria gráfico temporal
                df_plot = pd.DataFrame(valores_por_dia)
                fig = px.line(df_plot, title='Evolução dos Valores ao Longo do Tempo')
                results['grafico'] = fig

    except Exception as e:
        results['error'] = str(e)
    
    return results

def process_natural_language_query(query: str, df_cabecalho: pd.DataFrame = None, df_itens: pd.DataFrame = None) -> str:
    """Processa a consulta em linguagem natural e executa análises."""
    if not GEMINI_API_KEY:
        return "⚠️ Chave da API do Gemini não configurada!"
    
    try:
        # Executa as análises
        analysis_results = execute_analysis(query, df_cabecalho, df_itens)
        
        # Formata os resultados para o Gemini
        results_str = json.dumps(
            {k: v for k, v in analysis_results.items() if k != 'grafico'}, 
            indent=2, 
            ensure_ascii=False
        )
        
        # Consulta o Gemini
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(
            f"""Analise esta pergunta e os resultados da análise:
            
            Pergunta: {query}
            
            Resultados da análise: {results_str}
            
            Explique os resultados de forma clara e objetiva, citando os números encontrados."""
        )
        
        return response.text, analysis_results
    except Exception as e:
        return f"❌ Erro ao processar consulta: {str(e)}", {}

def main():
    st.title("Analisador de Notas Fiscais 📊")
    st.sidebar.title("Upload de Arquivos")

    # Upload de arquivo
    uploaded_file = st.sidebar.file_uploader("Escolha um arquivo ZIP", type=['zip'])
    
    # Mostra os DataFrames carregados
    if loader.get_all_dataframes():
        st.sidebar.subheader("Arquivos Carregados")
        for name, df in loader.get_all_dataframes().items():
            st.sidebar.text(f"📄 {name}: {df.shape[0]} linhas")
    
    if uploaded_file:
        with st.spinner('Processando arquivo...'):
            # Salva o arquivo temporariamente
            temp_path = os.path.join("data", uploaded_file.name)
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.getvalue())
            
            # Processa o arquivo
            success = loader.process_zip_file(temp_path)
            if success:
                st.success("✅ Arquivo processado com sucesso!")
                
                # Atualiza os agentes com os DataFrames
                dfs = loader.get_all_dataframes()
                df_cabecalho = None
                df_itens = None
                
                if dfs:
                    for name, df in dfs.items():
                        if 'cabecalho' in name.lower():
                            df_cabecalho = df
                            supplier_agent.set_dataframe(df)
                            st.info("📊 DataFrame de cabeçalho carregado")
                        elif 'item' in name.lower():
                            df_itens = df
                            item_agent.set_dataframe(df)
                            st.info("📦 DataFrame de itens carregado")
                    
                    # Interface de chat
                    st.header("💬 Pergunte sobre os dados")
                    st.markdown("""
                    Exemplos de perguntas:
                    - Qual fornecedor teve maior montante recebido?
                    - Qual produto teve maior quantidade vendida?
                    - Em qual período houve mais vendas?
                    - Qual a média de valor por nota fiscal?
                    """)
                    
                    user_query = st.text_input("Digite sua pergunta em linguagem natural:")
                    
                    if user_query and st.button("Analisar"):
                        with st.spinner('Analisando...'):
                            # Processa a pergunta e executa análises
                            response, analysis_results = process_natural_language_query(
                                user_query, 
                                df_cabecalho, 
                                df_itens
                            )
                            
                            # Mostra a resposta
                            st.write("🤖 Resposta:")
                            st.write(response)
                            
                            # Mostra o gráfico se disponível
                            if 'grafico' in analysis_results:
                                st.plotly_chart(analysis_results['grafico'])
                            
                            # Mostra dados detalhados em um expander
                            with st.expander("📊 Ver dados detalhados"):
                                st.json({k: v for k, v in analysis_results.items() if k != 'grafico'})
            else:
                st.error("❌ Erro ao processar o arquivo")

if __name__ == "__main__":
    main() 