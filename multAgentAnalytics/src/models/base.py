"""
Modelo base para todos os modelos do sistema.
"""

from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel as PydanticBaseModel, Field, ConfigDict

class BaseModel(PydanticBaseModel):
    """Modelo base com configurações comuns."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True
    )
    
    # Metadados comuns
    criado_em: datetime = Field(default_factory=datetime.now)
    atualizado_em: Optional[datetime] = None
    versao: str = Field(default="1.0.0")
    
    def atualizar_timestamp(self):
        """Atualiza o timestamp de modificação."""
        self.atualizado_em = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o modelo para dicionário."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Cria instância a partir de dicionário."""
        return cls(**data) 