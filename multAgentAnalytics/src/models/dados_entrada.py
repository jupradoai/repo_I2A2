"""
Modelo para dados de entrada consolidados.
"""

from datetime import date, datetime
from typing import Dict, List, Any
from decimal import Decimal
from pydantic import Field

from .base import BaseModel

class DadosEntrada(BaseModel):
    """Modelo para dados de entrada consolidados."""
    
    # Dados dos colaboradores ativos
    colaboradores_ativos: List[Dict[str, Any]] = Field(default_factory=list, description="Lista de colaboradores ativos")
    
    # Dados de férias
    colaboradores_ferias: List[Dict[str, Any]] = Field(default_factory=list, description="Lista de colaboradores em férias")
    
    # Dados de desligamento
    colaboradores_desligados: List[Dict[str, Any]] = Field(default_factory=list, description="Lista de colaboradores desligados")
    
    # Dados de admissão
    colaboradores_admissao: List[Dict[str, Any]] = Field(default_factory=list, description="Lista de colaboradores admitidos no mês")
    
    # Configurações de sindicato
    config_sindicatos: Dict[str, Decimal] = Field(default_factory=dict, description="Configuração de valores por sindicato")
    
    # Configurações de dias úteis
    dias_uteis_por_sindicato: Dict[str, int] = Field(default_factory=dict, description="Dias úteis por sindicato")
    
    # Dados de exclusões
    colaboradores_exterior: List[str] = Field(default_factory=list, description="Matrículas de colaboradores no exterior")
    colaboradores_estagio: List[str] = Field(default_factory=list, description="Matrículas de estagiários")
    colaboradores_aprendiz: List[str] = Field(default_factory=list, description="Matrículas de aprendizes")
    colaboradores_afastados: List[str] = Field(default_factory=list, description="Matrículas de colaboradores afastados")
    
    # Metadados
    data_processamento: date = Field(default_factory=date.today, description="Data de processamento")
    total_registros: int = Field(default=0, description="Total de registros processados")
    
    # Validações
    erros_validacao: List[Dict[str, Any]] = Field(default_factory=list, description="Lista de erros de validação")
    warnings: List[Dict[str, Any]] = Field(default_factory=list, description="Lista de warnings")
    
    # Campos para estrutura de saída
    competencia: str = Field(default="", description="Competência do mês (ex: 05.2025)")
    observacoes_gerais: str = Field(default="", description="Observações gerais do processamento")
    
    # Campos para totais calculados (adicionados para o agente Calculador)
    total_beneficios: Decimal = Field(default=Decimal('0'), description="Total dos benefícios VR/VA")
    total_custo_empresa: Decimal = Field(default=Decimal('0'), description="Total do custo para empresa")
    total_desconto_profissionais: Decimal = Field(default=Decimal('0'), description="Total do desconto dos profissionais")
    colaboradores_validos: int = Field(default=0, description="Total de colaboradores válidos para benefícios")
    
    # Campos para estatísticas finais
    total_colaboradores_processados: int = Field(default=0, description="Total de colaboradores processados")
    total_colaboradores_excluidos: int = Field(default=0, description="Total de colaboradores excluídos")
    percentual_cobertura: Decimal = Field(default=Decimal('0'), description="Percentual de cobertura dos benefícios")
    
    # Campos para controle de processamento
    processamento_concluido: bool = Field(default=False, description="Se o processamento foi concluído")
    timestamp_processamento: datetime = Field(default_factory=datetime.now, description="Timestamp do processamento")
    
    def adicionar_colaborador_ativo(self, dados: Dict[str, Any]):
        """Adiciona um colaborador ativo."""
        # Adiciona campos padrão se não existirem
        dados.setdefault('ativo', True)
        dados.setdefault('elegivel', True)
        dados.setdefault('dias_trabalhados', 0)
        dados.setdefault('dias_uteis', 0)
        dados.setdefault('valor_vr', 0)
        dados.setdefault('valor_total_beneficio', 0)
        dados.setdefault('custo_empresa', 0)
        dados.setdefault('desconto_profissional', 0)
        dados.setdefault('em_ferias', False)
        dados.setdefault('data_desligamento', None)
        dados.setdefault('data_admissao', None)
        dados.setdefault('observacoes', '')
        
        # Campos obrigatórios das validações
        dados.setdefault('nome', '')
        dados.setdefault('cpf', '')
        dados.setdefault('motivo_exclusao', '')
        
        self.colaboradores_ativos.append(dados)
        self.total_registros += 1
    
    def adicionar_colaborador_ferias(self, dados: Dict[str, Any]):
        """Adiciona um colaborador em férias."""
        self.colaboradores_ferias.append(dados)
    
    def adicionar_colaborador_desligado(self, dados: Dict[str, Any]):
        """Adiciona um colaborador desligado."""
        self.colaboradores_desligados.append(dados)
    
    def adicionar_colaborador_admissao(self, dados: Dict[str, Any]):
        """Adiciona um colaborador admitido."""
        self.colaboradores_admissao.append(dados)
    
    def configurar_sindicato(self, nome_sindicato: str, valor_diario: Decimal):
        """Configura o valor diário para um sindicato."""
        self.config_sindicatos[nome_sindicato] = valor_diario
    
    def configurar_dias_uteis(self, nome_sindicato: str, dias_uteis: int):
        """Configura os dias úteis para um sindicato."""
        self.dias_uteis_por_sindicato[nome_sindicato] = dias_uteis
    
    def adicionar_exclusao_exterior(self, matricula: str):
        """Adiciona uma matrícula para exclusão por trabalho no exterior."""
        if matricula not in self.colaboradores_exterior:
            self.colaboradores_exterior.append(matricula)
    
    def adicionar_exclusao_estagio(self, matricula: str):
        """Adiciona uma matrícula para exclusão por ser estagiário."""
        if matricula not in self.colaboradores_estagio:
            self.colaboradores_estagio.append(matricula)
    
    def adicionar_exclusao_aprendiz(self, matricula: str):
        """Adiciona uma matrícula para exclusão por ser aprendiz."""
        if matricula not in self.colaboradores_aprendiz:
            self.colaboradores_aprendiz.append(matricula)
    
    def adicionar_exclusao_afastado(self, matricula: str):
        """Adiciona uma matrícula para exclusão por afastamento."""
        if matricula not in self.colaboradores_afastados:
            self.colaboradores_afastados.append(matricula)
    
    def adicionar_erro_validacao(self, tipo: str, descricao: str, dados: Dict[str, Any] = None):
        """Adiciona um erro de validação."""
        erro = {
            "tipo": tipo,
            "descricao": descricao,
            "timestamp": datetime.now(),
            "dados": dados or {}
        }
        self.erros_validacao.append(erro)
    
    def adicionar_warning(self, tipo: str, descricao: str, dados: Dict[str, Any] = None):
        """Adiciona um warning."""
        warning = {
            "tipo": tipo,
            "descricao": descricao,
            "timestamp": datetime.now(),
            "dados": dados or {}
        }
        self.warnings.append(warning)
    
    def definir_competencia(self, competencia: str):
        """Define a competência do mês."""
        self.competencia = competencia
    
    def adicionar_observacao_geral(self, observacao: str):
        """Adiciona uma observação geral."""
        if self.observacoes_gerais:
            self.observacoes_gerais += f" | {observacao}"
        else:
            self.observacoes_gerais = observacao
    
    # Métodos para atualizar totais calculados
    def atualizar_totais_beneficios(self, total_beneficios: Decimal, total_custo_empresa: Decimal, total_desconto_profissionais: Decimal):
        """Atualiza os totais dos benefícios calculados."""
        self.total_beneficios = total_beneficios
        self.total_custo_empresa = total_custo_empresa
        self.total_desconto_profissionais = total_desconto_profissionais
    
    def atualizar_estatisticas_colaboradores(self, total_validos: int, total_excluidos: int):
        """Atualiza as estatísticas de colaboradores."""
        self.colaboradores_validos = total_validos
        self.total_colaboradores_excluidos = total_excluidos
        self.total_colaboradores_processados = self.total_registros
        
        # Calcula percentual de cobertura
        if self.total_registros > 0:
            self.percentual_cobertura = Decimal(str(total_validos)) / Decimal(str(self.total_registros)) * Decimal('100')
    
    def marcar_processamento_concluido(self):
        """Marca o processamento como concluído."""
        self.processamento_concluido = True
        self.timestamp_processamento = datetime.now()
    
    def obter_resumo_processamento(self) -> Dict[str, Any]:
        """Retorna um resumo completo do processamento."""
        return {
            "competencia": self.competencia,
            "total_colaboradores": self.total_registros,
            "colaboradores_validos": self.colaboradores_validos,
            "colaboradores_excluidos": self.total_colaboradores_excluidos,
            "percentual_cobertura": float(self.percentual_cobertura),
            "total_beneficios": float(self.total_beneficios),
            "total_custo_empresa": float(self.total_custo_empresa),
            "total_desconto_profissionais": float(self.total_desconto_profissionais),
            "processamento_concluido": self.processamento_concluido,
            "timestamp_processamento": self.timestamp_processamento.isoformat() if self.timestamp_processamento else None
        } 

    def obter_matriculas_excluidas(self) -> List[str]:
        """Retorna lista de matrículas excluídas."""
        matriculas_excluidas = set()
        
        # Adiciona matrículas do exterior
        for matricula in self.colaboradores_exterior:
            matriculas_excluidas.add(str(matricula))
        
        # Adiciona matrículas de estágio
        for matricula in self.colaboradores_estagio:
            matriculas_excluidas.add(str(matricula))
        
        # Adiciona matrículas de aprendiz
        for matricula in self.colaboradores_aprendiz:
            matriculas_excluidas.add(str(matricula))
        
        # Adiciona matrículas de afastados
        for matricula in self.colaboradores_afastados:
            matriculas_excluidas.add(str(matricula))
        
        return list(matriculas_excluidas) 