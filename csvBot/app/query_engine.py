import pandas as pd
from typing import Dict, Any, List
import re
import ast
import json

class QueryEngine:
    def __init__(self):
        self.available_operations = {
            'sum': pd.DataFrame.sum,
            'mean': pd.DataFrame.mean,
            'count': pd.DataFrame.count,
            'max': pd.DataFrame.max,
            'min': pd.DataFrame.min,
            'groupby': pd.DataFrame.groupby,
            'sort_values': pd.DataFrame.sort_values,
            'head': pd.DataFrame.head,
            'tail': pd.DataFrame.tail,
            'value_counts': pd.Series.value_counts,
            'merge': pd.merge
        }

    def parse_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """
        Interpreta a resposta estruturada do modelo
        """
        try:
            # Procura por seções específicas na resposta
            sections = {
                'dataframes': self._extract_section(analysis_text, "DataFrames necessários"),
                'columns': self._extract_section(analysis_text, "Colunas"),
                'code': self._extract_section(analysis_text, "Código pandas"),
                'format': self._extract_section(analysis_text, "Formatação")
            }
            
            return sections
        except Exception as e:
            raise ValueError(f"Erro ao interpretar análise: {str(e)}")

    def _extract_section(self, text: str, section_name: str) -> str:
        """
        Extrai uma seção específica da resposta do modelo
        """
        pattern = f"{section_name}.*?(?=(?:[1-4]\.|$))"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(0)
            # Remove o nome da seção e limpa o texto
            content = re.sub(f"{section_name}[:\s]*", "", content, flags=re.IGNORECASE)
            return content.strip()
        return ""

    def execute_query(self, parsed_analysis: Dict[str, Any], dataframes: Dict[str, pd.DataFrame]) -> Any:
        """
        Executa a análise nos DataFrames
        """
        try:
            # Prepara o ambiente de execução
            local_vars = {
                'pd': pd,
                **dataframes
            }

            # Obtém o código pandas da análise
            code = parsed_analysis.get('code', '')
            if not code:
                raise ValueError("Código pandas não encontrado na análise")

            # Executa o código de forma segura
            result = self._safe_execute(code, local_vars)

            # Formata o resultado conforme especificado
            return self._format_result(result, parsed_analysis.get('format', ''))

        except Exception as e:
            raise RuntimeError(f"Erro ao executar consulta: {str(e)}")

    def _safe_execute(self, code: str, local_vars: Dict[str, Any]) -> Any:
        """
        Executa o código pandas de forma segura
        """
        # Lista de operações permitidas
        allowed_ops = set(self.available_operations.keys())

        # Verifica se o código contém apenas operações permitidas
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr not in allowed_ops:
                        raise ValueError(f"Operação não permitida: {node.func.attr}")

        # Executa o código
        return eval(code, {"__builtins__": {}}, local_vars)

    def _format_result(self, result: Any, format_instructions: str) -> str:
        """
        Formata o resultado conforme as instruções
        """
        if isinstance(result, pd.DataFrame):
            # Se for um DataFrame, converte para uma tabela formatada
            return result.to_string()
        elif isinstance(result, pd.Series):
            # Se for uma Series, converte para uma lista formatada
            return result.to_string()
        elif isinstance(result, (float, int)):
            # Se for um número, formata com 2 casas decimais
            return f"{result:.2f}"
        else:
            # Para outros tipos, converte para string
            return str(result)

    def validate_query(self, query: str, dataframes: Dict[str, pd.DataFrame]) -> bool:
        """
        Valida se a consulta pode ser executada com os DataFrames disponíveis
        """
        try:
            # Verifica se os DataFrames mencionados existem
            for df_name in dataframes.keys():
                if df_name in query and df_name not in dataframes:
                    return False
            return True
        except Exception:
            return False
