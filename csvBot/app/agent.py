import os
import google.generativeai as genai
from typing import Dict, Any
import pandas as pd
from .query_engine import QueryEngine
import logging

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryAgent:
    def __init__(self):
        # Configuração do Gemini
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            logger.error("GOOGLE_API_KEY não encontrada nas variáveis de ambiente")
            raise ValueError("GOOGLE_API_KEY não encontrada nas variáveis de ambiente")
        
        logger.info("Inicializando modelo Gemini")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.query_engine = QueryEngine()

    def analyze_query(self, query: str, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Analisa a pergunta do usuário e determina como processá-la
        """
        try:
            logger.info(f"Analisando pergunta: {query}")
            
            # Construir o contexto para o modelo
            context = self._build_context(dataframes)
            logger.info("Contexto construído com sucesso")
            
            # Prompt para o modelo
            prompt = f"""
            Você é um assistente especializado em análise de dados de notas fiscais. Use os dados disponíveis para responder à pergunta.

            Especificações dos dados:
            - Campos separados por vírgulas
            - Valores decimais usam ponto como separador
            - Datas estão no formato AAAA-MM-DD HH:MN:SS
            - Valores monetários estão nas colunas 'VALOR NOTA FISCAL' e 'VALOR TOTAL'

            Dados disponíveis:
            {context}

            Pergunta: {query}

            Responda no seguinte formato:

            1. DataFrames necessários:
            [Liste apenas os nomes dos DataFrames que serão usados]

            2. Colunas relevantes:
            [Liste apenas as colunas que serão usadas]

            3. Código pandas:
            [IMPORTANTE: Gere apenas UMA operação por vez.
             Para análises complexas, sugira ao usuário fazer várias perguntas separadas.
             Exemplo de operações permitidas:
             - len(df)
             - df['coluna'].value_counts()
             - df.groupby('coluna')['valor'].sum()
             - df['coluna'].mean()
             NÃO use pd.DataFrame() ou operações complexas.]

            4. Formatação:
            [Como mostrar o resultado: tabela, número ou texto]

            Regras:
            - Use apenas operações simples: len(), value_counts(), groupby(), sum(), mean(), max(), min()
            - Uma operação por vez
            - Não use criação de DataFrames
            - Não use pd.concat ou merge
            - Use os nomes exatos dos DataFrames
            - Para contagens use len()
            """

            logger.info("Enviando prompt para o modelo")
            response = self.model.generate_content(prompt)
            logger.info("Resposta recebida do modelo")
            logger.info(f"Resposta:\n{response.text}")
            
            # Processar e estruturar a resposta usando o QueryEngine
            result = self.query_engine.parse_analysis(response.text)
            logger.info("Análise processada com sucesso")
            return result

        except Exception as e:
            logger.error(f"Erro ao analisar query: {str(e)}")
            raise

    def _build_context(self, dataframes: Dict[str, pd.DataFrame]) -> str:
        """
        Constrói uma descrição do contexto dos dados disponíveis
        """
        context = ["Análise dos dados disponíveis:"]
        
        for name, df in dataframes.items():
            context.append(f"\n📊 DataFrame: {name}")
            context.append(f"📋 Total de registros: {len(df)}")
            context.append(f"🔍 Colunas disponíveis:")
            
            # Análise das colunas
            for col in df.columns:
                dtype = df[col].dtype
                n_unique = df[col].nunique()
                n_null = df[col].isnull().sum()
                
                context.append(f"   - {col}")
                context.append(f"     Tipo: {dtype}")
                context.append(f"     Valores únicos: {n_unique}")
                if n_null > 0:
                    context.append(f"     Valores nulos: {n_null}")
                
                # Mostra alguns valores de exemplo para colunas não numéricas
                if dtype == 'object' or dtype.name.startswith('datetime'):
                    examples = df[col].dropna().head(3).tolist()
                    if examples:
                        context.append(f"     Exemplos: {examples}")
            
            context.append("\n📝 Primeiras linhas dos dados:")
            context.append(df.head(2).to_string())
            context.append("-" * 80)
        
        return "\n".join(context)

    def execute_analysis(self, analysis_result: Dict[str, Any], dataframes: Dict[str, pd.DataFrame]) -> str:
        """
        Executa a análise com base no resultado da interpretação
        """
        try:
            # Valida se a consulta pode ser executada
            if not self.query_engine.validate_query(str(analysis_result), dataframes):
                raise ValueError("Consulta inválida: DataFrames mencionados não existem")

            # Executa a análise usando o QueryEngine
            return self.query_engine.execute_query(analysis_result, dataframes)

        except Exception as e:
            return f"Erro ao executar análise: {str(e)}"
