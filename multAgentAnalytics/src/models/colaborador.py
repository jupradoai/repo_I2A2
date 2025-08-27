"""
Modelo de dados para colaborador.
"""

from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import Field, validator

from .base import BaseModel

class Colaborador(BaseModel):
    """Modelo de dados para colaborador."""
    
    # Identificação básica
    matricula: str = Field(..., description="Matrícula do colaborador")
    nome: str = Field(..., description="Nome completo do colaborador")
    cpf: Optional[str] = Field(None, description="CPF do colaborador")
    
    # Informações de contrato
    data_admissao: date = Field(..., description="Data de admissão")
    data_desligamento: Optional[date] = Field(None, description="Data de desligamento")
    cargo: str = Field(..., description="Cargo/função do colaborador")
    sindicato: str = Field(..., description="Sindicato vinculado")
    
    # Informações de benefícios
    valor_vr: Optional[Decimal] = Field(None, description="Valor do Vale Refeição")
    valor_va: Optional[Decimal] = Field(None, description="Valor do Vale Alimentação")
    dias_uteis: int = Field(default=0, description="Dias úteis no mês")
    dias_trabalhados: int = Field(default=0, description="Dias efetivamente trabalhados")
    
    # Status e exclusões
    ativo: bool = Field(default=True, description="Se está ativo")
    em_ferias: bool = Field(default=False, description="Se está em férias")
    afastado: bool = Field(default=False, description="Se está afastado")
    no_exterior: bool = Field(default=False, description="Se trabalha no exterior")
    
    # Cálculos
    valor_total_beneficio: Optional[Decimal] = Field(None, description="Valor total do benefício")
    custo_empresa: Optional[Decimal] = Field(None, description="Custo para a empresa (80%)")
    desconto_profissional: Optional[Decimal] = Field(None, description="Desconto do profissional (20%)")
    
    # Validações
    elegivel_beneficio: bool = Field(default=True, description="Se é elegível ao benefício")
    motivo_exclusao: Optional[str] = Field(None, description="Motivo da exclusão se aplicável")
    
    @validator('matricula')
    def validar_matricula(cls, v):
        """Valida se a matrícula não está vazia."""
        if not v or not v.strip():
            raise ValueError('Matrícula não pode estar vazia')
        return v.strip()
    
    @validator('nome')
    def validar_nome(cls, v):
        """Valida se o nome não está vazio."""
        if not v or not v.strip():
            raise ValueError('Nome não pode estar vazio')
        return v.strip()
    
    @validator('data_admissao')
    def validar_data_admissao(cls, v):
        """Valida se a data de admissão é válida."""
        if v > date.today():
            raise ValueError('Data de admissão não pode ser futura')
        return v
    
    def calcular_beneficio(self, dias_uteis_mes: int, valor_diario: Decimal):
        """Calcula o benefício baseado nos dias úteis."""
        self.dias_uteis = dias_uteis_mes
        self.valor_vr = valor_diario
        
        # Ajusta dias trabalhados baseado em férias e afastamentos
        if self.em_ferias or self.afastado:
            self.dias_trabalhados = 0
        elif self.data_desligamento:
            # Calcula dias até o desligamento
            from datetime import date
            hoje = date.today()
            if self.data_desligamento <= hoje:
                self.dias_trabalhados = 0
            else:
                # Implementar lógica de cálculo de dias úteis até desligamento
                self.dias_trabalhados = dias_uteis_mes
        else:
            self.dias_trabalhados = dias_uteis_mes
        
        # Calcula valores
        self.valor_total_beneficio = self.valor_vr * self.dias_trabalhados
        self.custo_empresa = self.valor_total_beneficio * Decimal('0.80')
        self.desconto_profissional = self.valor_total_beneficio * Decimal('0.20')
    
    def verificar_elegibilidade(self):
        """Verifica se o colaborador é elegível ao benefício."""
        cargos_excluidos = ['diretor', 'estagiário', 'aprendiz']
        cargo_lower = self.cargo.lower()
        
        if any(cargo_excluido in cargo_lower for cargo_excluido in cargos_excluidos):
            self.elegivel_beneficio = False
            self.motivo_exclusao = f"Cargo excluído: {self.cargo}"
            return False
        
        if self.no_exterior:
            self.elegivel_beneficio = False
            self.motivo_exclusao = "Trabalha no exterior"
            return False
        
        if self.afastado:
            self.elegivel_beneficio = False
            self.motivo_exclusao = "Colaborador afastado"
            return False
        
        return True 