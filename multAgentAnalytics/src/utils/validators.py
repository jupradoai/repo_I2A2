"""
Utilitários essenciais para validação de dados.
"""

import re
import logging
from datetime import datetime, date
from typing import Any

logger = logging.getLogger(__name__)

class DataValidator:
    """Utilitários essenciais para validação de dados."""
    
    @staticmethod
    def validar_matricula(matricula: str) -> bool:
        """Valida se uma matrícula é válida."""
        try:
            if not matricula or not isinstance(matricula, str):
                return False
            
            # Remove espaços em branco
            matricula = matricula.strip()
            
            # Verifica se não está vazia
            if not matricula:
                return False
            
            # Verifica se tem pelo menos 3 caracteres
            if len(matricula) < 3:
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Erro ao validar matrícula {matricula}: {e}")
            return False
    
    @staticmethod
    def validar_data(data: Any) -> bool:
        """Valida se uma data é válida."""
        try:
            if isinstance(data, (datetime, date)):
                return True
            
            if isinstance(data, str):
                # Tenta diferentes formatos de data
                formatos = [
                    '%d/%m/%Y',
                    '%d-%m-%Y',
                    '%Y-%m-%d'
                ]
                
                for formato in formatos:
                    try:
                        datetime.strptime(data, formato)
                        return True
                    except ValueError:
                        continue
                
                return False
            
            return False
            
        except Exception as e:
            logger.warning(f"Erro ao validar data {data}: {e}")
            return False
    
    @staticmethod
    def validar_valor_monetario(valor: Any) -> bool:
        """Valida se um valor monetário é válido."""
        try:
            if isinstance(valor, (int, float, Decimal)):
                return valor >= 0
            
            if isinstance(valor, str):
                # Remove símbolos de moeda e espaços
                valor_limpo = re.sub(r'[R$\s.,]', '', valor)
                if valor_limpo:
                    return float(valor_limpo) >= 0
            
            return False
            
        except Exception as e:
            logger.warning(f"Erro ao validar valor monetário {valor}: {e}")
            return False
    
    @staticmethod
    def validar_campo_obrigatorio(valor: Any, nome_campo: str) -> bool:
        """Valida se um campo obrigatório está preenchido."""
        try:
            if valor is None:
                return False
            
            if isinstance(valor, str):
                return valor.strip() != ''
            
            if isinstance(valor, (int, float, Decimal)):
                return True
            
            if isinstance(valor, (datetime, date)):
                return True
            
            return bool(valor)
            
        except Exception as e:
            logger.warning(f"Erro ao validar campo obrigatório {nome_campo}: {e}")
            return False 