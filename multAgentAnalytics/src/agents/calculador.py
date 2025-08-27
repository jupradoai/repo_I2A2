"""
Agente Calculador - Executa cálculos de VR/VA.
"""

from typing import Any
from decimal import Decimal

from .base import BaseAgente
from models.dados_entrada import DadosEntrada

class AgenteCalculador(BaseAgente):
    """Calcula benefícios VR/VA aplicando regras de negócio."""
    
    def __init__(self, settings):
        super().__init__(settings, "Calculador")
        
    async def _executar_agente(self, dados_entrada: DadosEntrada) -> DadosEntrada:
        """Executa cálculos de benefícios."""
        try:
            self.logger.info("🧮 Calculando benefícios VR/VA...")
            
            # Aplica regras de negócio
            self._aplicar_regras_desligamento(dados_entrada)
            self._aplicar_regras_ferias(dados_entrada)
            
            # Calcula benefícios
            self._calcular_beneficios(dados_entrada)
            self._calcular_totais(dados_entrada)
            
            self.logger.info("✅ Cálculos concluídos")
            return dados_entrada
            
        except Exception as e:
            self.logger.error(f"❌ Erro nos cálculos: {e}")
            raise
    
    def _aplicar_regras_desligamento(self, dados: DadosEntrada):
        """Aplica regra de desligamento (antes/depois do dia 15)."""
        for colaborador in dados.colaboradores_ativos:
            if not colaborador.get('ativo', True):
                data_desligamento = colaborador.get('data_desligamento')
                if data_desligamento:
                    try:
                        dia = data_desligamento.day if hasattr(data_desligamento, 'day') else 15
                        
                        if dia <= self.settings.DIA_LIMITE_DESLIGAMENTO:
                            # Desligado antes do dia 15 - não elegível
                            colaborador['dias_trabalhados'] = 0
                            colaborador['elegivel'] = False
                        else:
                            # Desligado após dia 15 - elegível proporcionalmente
                            colaborador['dias_trabalhados'] = dia - 1
                            colaborador['elegivel'] = True
                    except:
                        colaborador['dias_trabalhados'] = 0
                        colaborador['elegivel'] = False
        
        self.logger.info("✅ Regras de desligamento aplicadas")
    
    def _aplicar_regras_ferias(self, dados: DadosEntrada):
        """Aplica regras de férias."""
        for colaborador in dados.colaboradores_ativos:
            if colaborador.get('em_ferias', False):
                colaborador['dias_trabalhados'] = 0
                colaborador['elegivel'] = False
        
        self.logger.info("✅ Regras de férias aplicadas")
    
    def _calcular_beneficios(self, dados: DadosEntrada):
        """Calcula benefícios VR/VA para cada colaborador."""
        for colaborador in dados.colaboradores_ativos:
            if not colaborador.get('elegivel', True):
                continue
            
            sindicato = colaborador.get('sindicato', '')
            if not sindicato:
                continue
            
            # Obtém valor diário do estado/sindicato (float) e converte para Decimal
            valor_diario_float = dados.config_sindicatos.get(sindicato, 0)
            if not valor_diario_float:
                continue
            valor_diario = Decimal(str(valor_diario_float))
            
            # Obtém dias úteis do estado/sindicato
            dias_uteis = dados.dias_uteis_por_sindicato.get(sindicato, 0)
            if not dias_uteis or int(dias_uteis) <= 0:
                continue
            
            # Dias trabalhados: usa o informado; se None/vazio, usa dias_uteis (planilha)
            dt_raw = colaborador.get('dias_trabalhados')
            if dt_raw is None or (isinstance(dt_raw, str) and dt_raw.strip() == ''):
                dt_raw = dias_uteis
            try:
                # aceita int/float/str; normaliza para int
                dt_int = int(float(dt_raw))
            except Exception:
                dt_int = int(dias_uteis)
            if dt_int < 0:
                dt_int = 0
            
            # Calcula benefício com Decimal
            valor_total = valor_diario * Decimal(dt_int)
            
            # Aplica percentuais (80% empresa, 20% profissional) com Decimal
            perc_empresa = Decimal(str(self.settings.CUSTO_EMPRESA_PERCENTUAL))
            perc_prof = Decimal(str(self.settings.CUSTO_PROFISSIONAL_PERCENTUAL))
            custo_empresa = valor_total * perc_empresa
            desconto_profissional = valor_total * perc_prof
            
            # Atualiza dados do colaborador (mantém Decimal)
            colaborador.update({
                'valor_vr': valor_diario,
                'dias_uteis': int(dias_uteis),
                'dias_trabalhados': dt_int,
                'valor_total_beneficio': valor_total,
                'custo_empresa': custo_empresa,
                'desconto_profissional': desconto_profissional
            })
        
        self.logger.info("✅ Benefícios calculados")
    
    def _calcular_totais(self, dados: DadosEntrada):
        """Calcula totais gerais."""
        total_beneficios = Decimal('0')
        total_custo_empresa = Decimal('0')
        total_desconto_profissionais = Decimal('0')
        colaboradores_validos = 0
        
        for colaborador in dados.colaboradores_ativos:
            if colaborador.get('elegivel', True):
                colaboradores_validos += 1
                
                valor_total = colaborador.get('valor_total_beneficio', Decimal('0'))
                custo_empresa = colaborador.get('custo_empresa', Decimal('0'))
                desconto_profissional = colaborador.get('desconto_profissional', Decimal('0'))
                
                # Garante Decimal
                if not isinstance(valor_total, Decimal):
                    valor_total = Decimal(str(valor_total))
                if not isinstance(custo_empresa, Decimal):
                    custo_empresa = Decimal(str(custo_empresa))
                if not isinstance(desconto_profissional, Decimal):
                    desconto_profissional = Decimal(str(desconto_profissional))
                
                total_beneficios += valor_total
                total_custo_empresa += custo_empresa
                total_desconto_profissionais += desconto_profissional
        
        # Atualiza totais
        dados.total_beneficios = total_beneficios
        dados.total_custo_empresa = total_custo_empresa
        dados.total_desconto_profissionais = total_desconto_profissionais
        dados.colaboradores_validos = colaboradores_validos
        
        self.logger.info(f"✅ Totais: {colaboradores_validos} válidos, R$ {total_beneficios:,.2f} total") 