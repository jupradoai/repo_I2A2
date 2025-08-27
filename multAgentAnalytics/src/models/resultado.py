"""
Modelo para resultado do processamento.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import Field

from .base import BaseModel

class ResultadoProcessamento(BaseModel):
    """Modelo para resultado do processamento."""
    
    # Status geral
    sucesso: bool = Field(..., description="Se o processamento foi bem-sucedido")
    mensagem: str = Field(..., description="Mensagem descritiva do resultado")
    
    # Informações de processamento
    timestamp_inicio: datetime = Field(..., description="Timestamp de início")
    timestamp_fim: Optional[datetime] = Field(None, description="Timestamp de fim")
    duracao_segundos: Optional[float] = Field(None, description="Duração em segundos")
    
    # Estatísticas
    total_colaboradores: int = Field(default=0, description="Total de colaboradores processados")
    colaboradores_validos: int = Field(default=0, description="Colaboradores válidos")
    colaboradores_excluidos: int = Field(default=0, description="Colaboradores excluídos")
    erros_encontrados: int = Field(default=0, description="Total de erros encontrados")
    
    # Valores calculados
    valor_total_beneficios: Optional[Decimal] = Field(None, description="Valor total dos benefícios")
    custo_total_empresa: Optional[Decimal] = Field(None, description="Custo total para empresa")
    desconto_total_profissionais: Optional[Decimal] = Field(None, description="Desconto total dos profissionais")
    
    # Arquivos e saída
    arquivo_saida: Optional[str] = Field(None, description="Caminho do arquivo de saída")
    arquivo_log: Optional[str] = Field(None, description="Caminho do arquivo de log")
    
    # Detalhes de erro
    erro: Optional[str] = Field(None, description="Descrição do erro se houver")
    stack_trace: Optional[str] = Field(None, description="Stack trace do erro")
    detalhes_erros: List[Dict[str, Any]] = Field(default_factory=list, description="Lista detalhada de erros")
    
    # Metadados
    versao_sistema: str = Field(default="1.0.0", description="Versão do sistema")
    configuracao_usada: Dict[str, Any] = Field(default_factory=dict, description="Configuração utilizada")
    
    def calcular_duracao(self):
        """Calcula a duração do processamento."""
        if self.timestamp_fim and self.timestamp_inicio:
            self.duracao_segundos = (self.timestamp_fim - self.timestamp_inicio).total_seconds()
    
    def finalizar_com_sucesso(self, arquivo_saida: str, arquivo_log: str):
        """Finaliza o processamento com sucesso."""
        self.timestamp_fim = datetime.now()
        self.calcular_duracao()
        self.arquivo_saida = arquivo_saida
        self.arquivo_log = arquivo_log
        self.sucesso = True
        self.mensagem = "Processamento concluído com sucesso"
    
    def finalizar_com_erro(self, erro: str, stack_trace: str = None):
        """Finaliza o processamento com erro."""
        self.timestamp_fim = datetime.now()
        self.calcular_duracao()
        self.sucesso = False
        self.erro = erro
        self.stack_trace = stack_trace
        self.mensagem = f"Erro durante o processamento: {erro}"
    
    def adicionar_erro_detalhado(self, tipo: str, descricao: str, dados: Dict[str, Any] = None):
        """Adiciona um erro detalhado à lista."""
        erro_detalhado = {
            "tipo": tipo,
            "descricao": descricao,
            "timestamp": datetime.now(),
            "dados": dados or {}
        }
        self.detalhes_erros.append(erro_detalhado)
        self.erros_encontrados += 1
    
    def atualizar_estatisticas(self, total: int, validos: int, excluidos: int):
        """Atualiza as estatísticas de processamento."""
        self.total_colaboradores = total
        self.colaboradores_validos = validos
        self.colaboradores_excluidos = excluidos
    
    def atualizar_valores_calculados(self, total_beneficios: Decimal, custo_empresa: Decimal, desconto_profissionais: Decimal):
        """Atualiza os valores calculados."""
        self.valor_total_beneficios = total_beneficios
        self.custo_total_empresa = custo_empresa
        self.desconto_total_profissionais = desconto_profissionais
    
    def to_summary(self) -> Dict[str, Any]:
        """Retorna um resumo do resultado."""
        return {
            "sucesso": self.sucesso,
            "mensagem": self.mensagem,
            "duracao_segundos": self.duracao_segundos,
            "total_colaboradores": self.total_colaboradores,
            "colaboradores_validos": self.colaboradores_validos,
            "colaboradores_excluidos": self.colaboradores_excluidos,
            "erros_encontrados": self.erros_encontrados,
            "valor_total_beneficios": str(self.valor_total_beneficios) if self.valor_total_beneficios else None,
            "arquivo_saida": self.arquivo_saida
        } 