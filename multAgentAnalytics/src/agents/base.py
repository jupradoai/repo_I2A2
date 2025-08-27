"""
Classe base para todos os agentes do sistema.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from datetime import datetime
from decimal import Decimal

from rich.console import Console
from rich.logging import RichHandler
from pydantic import Field

from config.settings import Settings

class BaseAgente(ABC):
    """Classe base para todos os agentes do sistema."""
    
    def __init__(self, settings: Settings, nome: str):
        """Inicializa o agente base."""
        self.settings = settings
        self.nome = nome
        self.console = Console()
        self.logger = self._setup_logger()
        self.iniciado_em: Optional[datetime] = None
        self.finalizado_em: Optional[datetime] = None
        self.status = "inicializado"
        self.erros: list = []
        self.warnings: list = []
        
    def _setup_logger(self) -> logging.Logger:
        """Configura o logger específico do agente."""
        logger = logging.getLogger(f"agente.{self.nome}")
        
        if not logger.handlers:
            # Handler para console rico
            console_handler = RichHandler(console=self.console, show_time=True)
            console_handler.setLevel(logging.INFO)
            
            # Handler para arquivo
            log_file = self.settings.LOGS_DIR / f"{self.nome}.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            
            # Formato
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)
            
            logger.addHandler(console_handler)
            logger.addHandler(file_handler)
            logger.setLevel(logging.DEBUG)
        
        return logger
    
    async def executar(self, dados_entrada: Any = None) -> Any:
        """Executa o agente de forma assíncrona."""
        try:
            self.iniciado_em = datetime.now()
            self.status = "executando"
            
            self.logger.info(f"🚀 Agente {self.nome} iniciando execução")
            self.console.print(f"[bold blue]▶️ {self.nome}[/bold blue] Iniciando...")
            
            # Execução específica do agente
            resultado = await self._executar_agente(dados_entrada)
            
            self.status = "concluido"
            self.finalizado_em = datetime.now()
            
            duracao = (self.finalizado_em - self.iniciado_em).total_seconds()
            self.logger.info(f"✅ Agente {self.nome} concluído em {duracao:.2f}s")
            self.console.print(f"[bold green]✅ {self.nome}[/bold green] Concluído em {duracao:.2f}s")
            
            return resultado
            
        except Exception as e:
            self.status = "erro"
            self.finalizado_em = datetime.now()
            self.erros.append(str(e))
            
            self.logger.error(f"❌ Erro no agente {self.nome}: {e}", exc_info=True)
            self.console.print(f"[bold red]❌ {self.nome}[/bold red] Erro: {e}")
            
            raise
    
    @abstractmethod
    async def _executar_agente(self, dados_entrada: Any) -> Any:
        """Método abstrato que deve ser implementado por cada agente."""
        pass
    
    def adicionar_erro(self, erro: str, dados: Dict[str, Any] = None):
        """Adiciona um erro ao agente."""
        erro_info = {
            "mensagem": erro,
            "timestamp": datetime.now(),
            "dados": dados or {}
        }
        self.erros.append(erro_info)
        self.logger.error(f"Erro: {erro}")
    
    def adicionar_warning(self, warning: str, dados: Dict[str, Any] = None):
        """Adiciona um warning ao agente."""
        warning_info = {
            "mensagem": warning,
            "timestamp": datetime.now(),
            "dados": dados or {}
        }
        self.warnings.append(warning_info)
        self.logger.warning(f"Warning: {warning}")
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas do agente."""
        return {
            "nome": self.nome,
            "status": self.status,
            "iniciado_em": self.iniciado_em.isoformat() if self.iniciado_em else None,
            "finalizado_em": self.finalizado_em.isoformat() if self.finalizado_em else None,
            "duracao_segundos": (
                (self.finalizado_em - self.iniciado_em).total_seconds() 
                if self.iniciado_em and self.finalizado_em else None
            ),
            "total_erros": len(self.erros),
            "total_warnings": len(self.warnings)
        }
    
    def limpar_estado(self):
        """Limpa o estado do agente para nova execução."""
        self.iniciado_em = None
        self.finalizado_em = None
        self.status = "inicializado"
        self.erros.clear()
        self.warnings.clear()
    
    def __str__(self) -> str:
        """Representação string do agente."""
        return f"Agente({self.nome}, status={self.status})"
    
    def __repr__(self) -> str:
        """Representação detalhada do agente."""
        return f"<{self.__class__.__name__}(nome='{self.nome}', status='{self.status}')>" 