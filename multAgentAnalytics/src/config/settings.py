"""
Configurações do Sistema Multiagente para VR/VA
===============================================
"""

from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class Settings(BaseModel):
    """Configurações do sistema."""
    
    # Diretórios base
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    OUTPUT_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "output")
    LOGS_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "logs")
    
    # Configurações de arquivos
    ARQUIVOS_ENTRADA: Dict[str, str] = {
        "ativos": "ATIVOS.xlsx",
        "ferias": "FÉRIAS.xlsx",
        "desligados": "DESLIGADOS.xlsx",
        "admissao": "ADMISSÃO ABRIL.xlsx",
        "sindicato_valor": "Base sindicato x valor.xlsx",
        "dias_uteis": "Base dias uteis.xlsx",
        "exterior": "EXTERIOR.xlsx",
        "estagio": "ESTÁGIO.xlsx",
        "aprendiz": "APRENDIZ.xlsx",
        "afastamentos": "AFASTAMENTOS.xlsx"
    }
    
    # Configurações de processamento
    MAX_WORKERS: int = 4
    CHUNK_SIZE: int = 1000
    TIMEOUT_PROCESSAMENTO: int = 300  # 5 minutos
    
    # Regras de negócio
    CUSTO_EMPRESA_PERCENTUAL: float = 0.80  # 80%
    CUSTO_PROFISSIONAL_PERCENTUAL: float = 0.20  # 20%
    DIA_LIMITE_DESLIGAMENTO: int = 15
    
    # Configuração de feriados reais para maio/2025
    FERIADOS_MAIO_2025: List[int] = [
        1,   # 1º de maio - Dia do Trabalhador (Nacional)
        8,   # 8 de maio - Dia da Vitória (Nacional)
        15,  # 15 de maio - Dia do Assistente Social (Nacional)
        22,  # 22 de maio - Dia do Apicultor (Nacional)
        29   # 29 de maio - Dia do Geógrafo (Nacional)
    ]
    
    # Feriados estaduais e municipais (exemplo para SP)
    FERIADOS_ESTADUAIS: Dict[str, List[int]] = {
        "SP": [1, 8, 15, 22, 29],  # Mesmo que nacional para SP
        "RJ": [1, 8, 15, 22, 29],  # Mesmo que nacional para RJ
        "MG": [1, 8, 15, 22, 29]   # Mesmo que nacional para MG
    }
    
    # Feriados municipais (exemplo para São Paulo)
    FERIADOS_MUNICIPAIS: Dict[str, List[int]] = {
        "SAO_PAULO": [1, 8, 15, 22, 29],  # Mesmo que nacional
        "RIO_JANEIRO": [1, 8, 15, 22, 29], # Mesmo que nacional
        "BELO_HORIZONTE": [1, 8, 15, 22, 29] # Mesmo que nacional
    }
    
    # Configuração de sindicatos reais com valores e acordos coletivos
    CONFIGURACAO_SINDICATOS: Dict[str, Dict[str, Any]] = {
        # Estados (para normalização de sindicatos por UF)
        "Paraná": {
            "valor_diario_vr": 25.00,
            "dias_uteis_mes": 23,
            "acordo_coletivo": "ESTADUAL",
            "percentual_empresa": 0.80,
            "percentual_profissional": 0.20,
            "regras_ferias": {"tipo": "parcial", "dias_minimos": 10, "dias_maximos": 30}
        },
        "Rio de Janeiro": {
            "valor_diario_vr": 26.00,
            "dias_uteis_mes": 22,
            "acordo_coletivo": "ESTADUAL",
            "percentual_empresa": 0.80,
            "percentual_profissional": 0.20,
            "regras_ferias": {"tipo": "parcial", "dias_minimos": 10, "dias_maximos": 30}
        },
        "Rio Grande do Sul": {
            "valor_diario_vr": 24.00,
            "dias_uteis_mes": 22,
            "acordo_coletivo": "ESTADUAL",
            "percentual_empresa": 0.80,
            "percentual_profissional": 0.20,
            "regras_ferias": {"tipo": "parcial", "dias_minimos": 10, "dias_maximos": 30}
        },
        "São Paulo": {
            "valor_diario_vr": 28.00,
            "dias_uteis_mes": 22,
            "acordo_coletivo": "ESTADUAL",
            "percentual_empresa": 0.80,
            "percentual_profissional": 0.20,
            "regras_ferias": {"tipo": "parcial", "dias_minimos": 10, "dias_maximos": 30}
        },
        "SINDICATO_METALURGICOS": {
            "valor_diario_vr": 25.50,
            "dias_uteis_mes": 23,
            "acordo_coletivo": "2024-2026",
            "percentual_empresa": 0.80,
            "percentual_profissional": 0.20,
            "regras_ferias": {
                "tipo": "parcial",
                "dias_minimos": 15,
                "dias_maximos": 30,
                "regra_especial": "Férias podem ser divididas em até 3 períodos"
            },
            "regras_especiais": [
                "Férias 30 dias", 
                "13º salário",
                "Admissão proporcional",
                "Desligamento proporcional"
            ]
        },
        "SINDICATO_QUIMICOS": {
            "valor_diario_vr": 28.00,
            "dias_uteis_mes": 23,
            "acordo_coletivo": "2024-2027",
            "percentual_empresa": 0.80,
            "percentual_profissional": 0.20,
            "regras_ferias": {
                "tipo": "integral",
                "dias_minimos": 30,
                "dias_maximos": 30,
                "regra_especial": "Férias devem ser gozadas integralmente"
            },
            "regras_especiais": [
                "Férias 30 dias", 
                "PLR",
                "Admissão proporcional",
                "Desligamento proporcional"
            ]
        },
        "SINDICATO_BANCARIOS": {
            "valor_diario_vr": 32.00,
            "dias_uteis_mes": 22,
            "acordo_coletivo": "2024-2025",
            "percentual_empresa": 0.85,
            "percentual_profissional": 0.15,
            "regras_ferias": {
                "tipo": "parcial",
                "dias_minimos": 10,
                "dias_maximos": 30,
                "regra_especial": "Férias podem ser divididas em até 4 períodos"
            },
            "regras_especiais": [
                "Férias 30 dias", 
                "PLR", 
                "Auxílio creche",
                "Admissão proporcional",
                "Desligamento proporcional"
            ]
        },
        "SINDICATO_COMERCIARIOS": {
            "valor_diario_vr": 22.00,
            "dias_uteis_mes": 23,
            "acordo_coletivo": "2024-2026",
            "percentual_empresa": 0.80,
            "percentual_profissional": 0.20,
            "regras_ferias": {
                "tipo": "parcial",
                "dias_minimos": 20,
                "dias_maximos": 30,
                "regra_especial": "Férias podem ser divididas em até 2 períodos"
            },
            "regras_especiais": [
                "Férias 30 dias", 
                "13º salário",
                "Admissão proporcional",
                "Desligamento proporcional"
            ]
        },
        "SINDICATO_TRANSPORTADORES": {
            "valor_diario_vr": 26.50,
            "dias_uteis_mes": 23,
            "acordo_coletivo": "2024-2027",
            "percentual_empresa": 0.80,
            "percentual_profissional": 0.20,
            "regras_ferias": {
                "tipo": "integral",
                "dias_minimos": 30,
                "dias_maximos": 30,
                "regra_especial": "Férias devem ser gozadas integralmente"
            },
            "regras_especiais": [
                "Férias 30 dias", 
                "Adicional noturno",
                "Admissão proporcional",
                "Desligamento proporcional"
            ]
        }
    }
    
    # Mapeamento de cargos para sindicatos
    MAPEAMENTO_CARGO_SINDICATO: Dict[str, str] = {
        "OPERADOR": "SINDICATO_METALURGICOS",
        "TECNICO": "SINDICATO_METALURGICOS",
        "ANALISTA": "SINDICATO_QUIMICOS",
        "ENGENHEIRO": "SINDICATO_QUIMICOS",
        "GERENTE": "SINDICATO_BANCARIOS",
        "SUPERVISOR": "SINDICATO_COMERCIARIOS",
        "VENDEDOR": "SINDICATO_COMERCIARIOS",
        "MOTORISTA": "SINDICATO_TRANSPORTADORES",
        "AUXILIAR": "SINDICATO_COMERCIARIOS"
    }
    
    # Configurações de logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "sistema_vr_va.log"
    
    # Configurações de validação
    VALIDACOES_OBRIGATORIAS: List[str] = [
        "matricula",
        "sindicato"
    ]
    
    # Configurações de saída
    FORMATO_SAIDA: str = "xlsx"
    NOME_ARQUIVO_SAIDA: str = "VR_MENSAL_SAIDA.xlsx"
    
    def __init__(self, **data):
        super().__init__(**data)
        # Garante que os diretórios existam
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True) 