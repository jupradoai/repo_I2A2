import os
import google.generativeai as genai
from typing import Dict, Any
import pandas as pd
from .query_engine import QueryEngine

class QueryAgent:
    def __init__(self):
        # Configuração do Gemini
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY não encontrada nas variáveis de ambiente")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.query_engine = QueryEngine()

    def analyze_query(self, query: str, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Analisa a pergunta do usuário e determina como processá-la
        """
        # Construir o contexto para o modelo
        context = self._build_context(dataframes)
        
        # Prompt para o modelo
        prompt = f"""
        Contexto dos dados disponíveis:
        {context}

        Pergunta do usuário:
        {query}

        Por favor, analise a pergunta e retorne no seguinte formato:

        1. DataFrames necessários:
        [Liste os DataFrames que serão usados]

        2. Colunas:
        [Liste as colunas relevantes de cada DataFrame]

        3. Código pandas:
        [Escreva o código pandas necessário para responder à pergunta]

        4. Formatação:
        [Especifique como o resultado deve ser formatado]

        Importante:
        - Use apenas operações pandas básicas (sum, mean, count, max, min, groupby, sort_values, head, tail, value_counts, merge)
        - O código deve ser executável
        - Use os nomes exatos dos DataFrames e colunas
        - Não use funções personalizadas
        """

        # Obter resposta do modelo
        response = self.model.generate_content(prompt)
        
        # Processar e estruturar a resposta usando o QueryEngine
        return self.query_engine.parse_analysis(response.text)

    def _build_context(self, dataframes: Dict[str, pd.DataFrame]) -> str:
        """
        Constrói uma descrição do contexto dos dados disponíveis
        """
        context = []
        for name, df in dataframes.items():
            context.append(f"\nDataFrame: {name}")
            context.append(f"Colunas: {', '.join(df.columns)}")
            context.append(f"Linhas: {len(df)}")
            context.append("Exemplo dos primeiros registros:")
            context.append(df.head(3).to_string())
            context.append("-" * 50)
        
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
