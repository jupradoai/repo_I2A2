"""
Utilitários para configuração de logging.
"""

import logging
import sys
from pathlib import Path
from rich.logging import RichHandler
from rich.console import Console

def setup_logging(
    level: str = "INFO",
    log_file: str = "sistema_vr_va.log",
    log_dir: Path = None
):
    """Configura o sistema de logging."""
    
    # Cria diretório de logs se não existir
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = log_dir / log_file
    else:
        log_file_path = Path(log_file)
    
    # Configura logging básico
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # Handler para arquivo
            logging.FileHandler(log_file_path, encoding='utf-8'),
            # Handler para console com Rich
            RichHandler(
                console=Console(),
                show_time=True,
                show_path=False,
                markup=True
            )
        ]
    )
    
    # Configura loggers específicos
    loggers = [
        'src.agents',
        'src.services',
        'src.utils'
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, level.upper()))
    
    # Log de inicialização
    logging.info("🚀 Sistema de logging configurado com sucesso")
    logging.info(f"📁 Arquivo de log: {log_file_path}")
    logging.info(f"🔧 Nível de log: {level}")
    
    return logging.getLogger(__name__) 