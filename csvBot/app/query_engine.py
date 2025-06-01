import pandas as pd
from typing import Dict, Any, List
import re
import ast
import json
import logging

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            logger.info("Analisando resposta do modelo:")
            logger.info(f"Texto recebido:\n{analysis_text}")
            
            # Procura por seções específicas na resposta
            sections = {
                'dataframes': self._extract_section(analysis_text, "DataFrames necessários"),
                'columns': self._extract_section(analysis_text, "Colunas"),
                'code': self._extract_section(analysis_text, "Código pandas"),
                'format': self._extract_section(analysis_text, "Formatação")
            }
            
            logger.info("Seções extraídas:")
            for key, value in sections.items():
                logger.info(f"{key}: {value}")
            
            return sections
        except Exception as e:
            logger.error(f"Erro ao interpretar análise: {str(e)}")
            raise ValueError(f"Erro ao interpretar análise: {str(e)}")

    def _extract_section(self, text: str, section_name: str) -> str:
        """
        Extrai uma seção específica da resposta do modelo
        """
        pattern = f"{section_name}.*?(?=(?:[1-4]\\.|$))"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(0)
            # Remove o nome da seção e limpa o texto
            content = re.sub(f"{section_name}[:\\s]*", "", content, flags=re.IGNORECASE)
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

            # Obtém o código pandas da análise e limpa marcadores markdown
            code = parsed_analysis.get('code', '').strip()
            # Remove marcadores markdown
            code = re.sub(r'```\w*\n?', '', code)
            code = code.strip()
            
            logger.info(f"Código limpo para execução: {code}")
            
            if not code:
                raise ValueError("Código pandas não encontrado na análise")

            # Verifica se é uma operação simples
            if '\n' in code or ';' in code:
                raise ValueError("Apenas uma operação simples por vez é permitida")

            # Verifica operações não permitidas
            if 'pd.DataFrame' in code or 'pd.concat' in code or 'merge' in code:
                raise ValueError("Operações complexas não são permitidas")

            # Executa o código
            try:
                ast.parse(code)
                logger.info(f"Executando código: {code}")
                result = eval(code, self._get_safe_exec_env(local_vars))
                logger.info("Código executado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao executar código: {str(e)}")
                raise

            # Formata o resultado
            formatted_result = self._format_result(result, parsed_analysis.get('format', ''))
            logger.info("Resultado formatado com sucesso")
            
            return formatted_result

        except Exception as e:
            logger.error(f"Erro ao executar consulta: {str(e)}")
            logger.error(f"Análise completa: {parsed_analysis}")
            raise RuntimeError(f"Erro ao executar consulta: {str(e)}")

    def _get_safe_exec_env(self, local_vars: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria um ambiente de execução seguro com funções permitidas
        """
        safe_builtins = {
            'len': len,
            'round': round
        }
        
        return {
            "__builtins__": safe_builtins,
            **local_vars
        }

    def _format_result(self, result: Any, format_instructions: str) -> str:
        """
        Formata o resultado conforme as instruções
        """
        try:
            if isinstance(result, pd.DataFrame):
                return result.to_string(index=True, float_format=lambda x: '{:,.2f}'.format(x) if isinstance(x, float) else str(x))
            elif isinstance(result, pd.Series):
                if result.dtype in ['float64', 'float32']:
                    return result.apply(lambda x: '{:,.2f}'.format(x)).to_string()
                return result.to_string()
            elif isinstance(result, (float, int)):
                return '{:,.2f}'.format(float(result))
            else:
                return str(result)
        except Exception as e:
            logger.error(f"Erro ao formatar resultado: {str(e)}")
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
