"""
Utilitários essenciais para manipulação de arquivos Excel.
"""

import pandas as pd
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

class ExcelUtils:
    """Utilitários essenciais para manipulação de arquivos Excel."""
    
    @staticmethod
    def ler_excel(arquivo: Path, aba: str = None, **kwargs) -> pd.DataFrame:
        """Lê um arquivo Excel e retorna um DataFrame."""
        try:
            if aba:
                df = pd.read_excel(arquivo, sheet_name=aba, **kwargs)
            else:
                df = pd.read_excel(arquivo, **kwargs)
            
            logger.debug(f"Arquivo Excel lido com sucesso: {arquivo}")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao ler arquivo Excel {arquivo}: {e}")
            raise
    
    @staticmethod
    def salvar_excel(
        df: pd.DataFrame,
        arquivo: Path,
        aba: str = "Sheet1",
        index: bool = False,
        **kwargs
    ):
        """Salva um DataFrame em um arquivo Excel."""
        try:
            with pd.ExcelWriter(arquivo, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=aba, index=index, **kwargs)
            
            logger.debug(f"DataFrame salvo com sucesso em: {arquivo}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar DataFrame em {arquivo}: {e}")
            raise
    
    @staticmethod
    def obter_nomes_abas(arquivo: Path) -> List[str]:
        """Retorna os nomes das abas de um arquivo Excel."""
        try:
            xl = pd.ExcelFile(arquivo)
            nomes_abas = xl.sheet_names
            xl.close()
            
            logger.debug(f"Abas encontradas em {arquivo}: {nomes_abas}")
            return nomes_abas
            
        except Exception as e:
            logger.error(f"Erro ao obter nomes das abas de {arquivo}: {e}")
            raise
    
    @staticmethod
    def validar_estrutura_excel(
        arquivo: Path,
        colunas_obrigatorias: List[str],
        aba: str = None
    ) -> bool:
        """Valida se um arquivo Excel tem a estrutura esperada."""
        try:
            df = ExcelUtils.ler_excel(arquivo, aba)
            
            colunas_arquivo = set(df.columns)
            colunas_obrigatorias_set = set(colunas_obrigatorias)
            
            colunas_faltantes = colunas_obrigatorias_set - colunas_arquivo
            
            if colunas_faltantes:
                logger.warning(f"Colunas obrigatórias faltando em {arquivo}: {colunas_faltantes}")
                return False
            
            logger.debug(f"Estrutura do arquivo {arquivo} validada com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao validar estrutura de {arquivo}: {e}")
            return False 