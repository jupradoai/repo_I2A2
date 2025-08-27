"""
Modelos de dados do sistema.
"""

from .base import BaseModel
from .colaborador import Colaborador
from .resultado import ResultadoProcessamento
from .dados_entrada import DadosEntrada

__all__ = [
    "BaseModel",
    "Colaborador", 
    "ResultadoProcessamento",
    "DadosEntrada"
] 