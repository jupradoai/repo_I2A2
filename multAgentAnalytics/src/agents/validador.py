"""
Agente Validador - Valida dados e regras de negócio.
"""

import asyncio
import logging
import time
from typing import Any, List, Dict
from decimal import Decimal
from datetime import datetime

from .base import BaseAgente
from models.dados_entrada import DadosEntrada

class AgenteValidador(BaseAgente):
    """Valida TODAS as regras de negócio e consistência dos dados."""
    
    def __init__(self, settings):
        super().__init__(settings, "Validador")
        
    async def _executar_agente(self, dados_entrada: DadosEntrada):
        """Executa o agente validador."""
        try:
            print("🔍 Iniciando validação dos dados...")
            inicio = time.time()
            
            # Listas acumuladoras para regras que retornam listas
            erros_list: List[str] = []
            warnings_list: List[str] = []
            
            # Regras que retornam listas de erros/warnings
            erros_list.extend(self._validar_exterior(dados_entrada))
            erros_list.extend(self._validar_estagio(dados_entrada))
            erros_list.extend(self._validar_aprendiz(dados_entrada))
            erros_list.extend(self._validar_afastados(dados_entrada))
            warnings_list.extend(self._validar_acordos_coletivos(dados_entrada))
            
            # Regras booleanas que registram via adicionar_erro/adicionar_warning
            self._validar_matriculas(dados_entrada)
            self._validar_consistencia(dados_entrada)
            self._validar_calculos(dados_entrada)
            self._validar_totais(dados_entrada)
            self._validar_ferias(dados_entrada)
            self._validar_desligamento_dia_15(dados_entrada)
            self._validar_desligamento_dia_16_plus(dados_entrada)
            self._validar_admitidos_mes(dados_entrada)
            self._validar_admitidos_mes_anterior(dados_entrada)
            self._validar_folha_ponto(dados_entrada)
            self._validar_diretores(dados_entrada)
            self._validar_calculo_pagamento(dados_entrada)
            self._validar_datas_quebradas(dados_entrada)
            
            # Consolida totais a partir do estado do agente + listas locais
            total_erros = len(self.erros) + len(erros_list)
            total_warnings = len(self.warnings) + len(warnings_list)
            duracao = time.time() - inicio
            
            print(f"✅ Validação concluída: {total_erros} erros, {total_warnings} warnings")
            
            return {
                'sucesso': total_erros == 0,
                'total_erros': total_erros,
                'total_warnings': total_warnings,
                'erros': erros_list,
                'warnings': warnings_list,
                'duracao_segundos': duracao,
                'registros_processados': len(dados_entrada.colaboradores_ativos)
            }
            
        except Exception as e:
            print(f"❌ Erro na validação: {e}")
            duracao = time.time() - inicio if 'inicio' in locals() else 0.0
            return {
                'sucesso': False,
                'erro': str(e),
                'total_erros': 1,
                'total_warnings': 0,
                'duracao_segundos': duracao,
                'registros_processados': 0
            }
    
    def _validar_matriculas(self, dados: DadosEntrada) -> bool:
        """Valida MATRICULA como campo obrigatório e consistência."""
        erros = 0
        
        for colaborador in dados.colaboradores_ativos:
            matricula = colaborador.get('matricula')
            if not matricula or str(matricula).strip() == '':
                self.adicionar_erro(f"MATRICULA obrigatória ausente")
                erros += 1
            
            # Validação de ativos (consolidada)
            if not colaborador.get('ativo', True):
                if not colaborador.get('observacoes', ''):
                    colaborador['observacoes'] = 'INATIVO'
        
        # Verifica duplicatas
        matriculas = [str(c.get('matricula', '')).strip() for c in dados.colaboradores_ativos if c.get('matricula')]
        if len(matriculas) != len(set(matriculas)):
            self.adicionar_erro("Matrículas duplicadas encontradas")
            erros += 1
        
        if erros > 0:
            self.logger.warning(f"⚠️ {erros} problemas com matrículas")
            return False
        
        self.logger.info("✅ Matrículas e ativos validados")
        return True
    
    def _validar_consistencia(self, dados: DadosEntrada) -> bool:
        """Verifica consistência entre arquivos e configurações de sindicatos."""
        erros = 0
        
        # Verifica se todos os sindicatos têm configuração
        sindicatos_ativos = set(c.get('sindicato') for c in dados.colaboradores_ativos if c.get('sindicato'))
        sindicatos_configurados = set(dados.config_sindicatos.keys())
        sindicatos_dias = set(dados.dias_uteis_por_sindicato.keys())
        
        # Sindicatos sem valor configurado
        sem_valor = sindicatos_ativos - sindicatos_configurados
        if sem_valor:
            self.adicionar_erro(f"Sindicatos sem valor: {list(sem_valor)}")
            erros += 1
        
        # Sindicatos sem dias úteis configurados
        sem_dias = sindicatos_ativos - sindicatos_dias
        if sem_dias:
            self.adicionar_erro(f"Sindicatos sem dias úteis: {list(sem_dias)}")
            erros += 1
        
        # Validação de valores por sindicato
        for sindicato, valor in dados.config_sindicatos.items():
            if valor <= 0:
                self.adicionar_erro(f"Valor inválido para {sindicato}: {valor}")
                erros += 1
        
        # Validação de dias úteis por sindicato
        for sindicato, dias in dados.dias_uteis_por_sindicato.items():
            if dias <= 0 or dias > 31:
                self.adicionar_erro(f"Dias úteis inválidos para {sindicato}: {dias}")
                erros += 1
        
        if erros > 0:
            self.logger.warning(f"⚠️ {erros} problemas de consistência")
            return False
        
        self.logger.info("✅ Consistência e sindicatos validados")
        return True
    
    def _validar_calculos(self, dados: DadosEntrada) -> bool:
        """Validação: CÁLCULOS - valores e benefícios."""
        erros = 0
        
        for colaborador in dados.colaboradores_ativos:
            if colaborador.get('elegivel', True):
                # Validação de valores VR
                valor_vr = colaborador.get('valor_vr', 0)
                dias_trabalhados = colaborador.get('dias_trabalhados', 0)
                valor_total = colaborador.get('valor_total_beneficio', 0)
                
                # Garante Decimal
                try:
                    from decimal import Decimal as _D
                    valor_total_d = valor_total if isinstance(valor_total, _D) else _D(str(valor_total))
                    custo_empresa_d = colaborador.get('custo_empresa', 0)
                    custo_empresa_d = custo_empresa_d if isinstance(custo_empresa_d, _D) else _D(str(custo_empresa_d))
                    desconto_prof_d = colaborador.get('desconto_profissional', 0)
                    desconto_prof_d = desconto_prof_d if isinstance(desconto_prof_d, _D) else _D(str(desconto_prof_d))
                except Exception:
                    # Se não conseguir converter, pula este registro
                    continue
                
                if valor_vr > 0 and dias_trabalhados > 0:
                    valor_calc = (valor_vr if isinstance(valor_vr, _D) else _D(str(valor_vr))) * _D(int(dias_trabalhados))
                    if abs(valor_calc - valor_total_d) > _D('0.01'):
                        self.adicionar_erro(f"Cálculo de benefício incorreto: {valor_vr} × {dias_trabalhados} ≠ {valor_total}")
                        erros += 1
                
                # Validação de percentuais empresa/profissional
                if valor_total_d > 0:
                    if abs(custo_empresa_d + desconto_prof_d - valor_total_d) > _D('0.01'):
                        self.adicionar_erro(f"Soma de percentuais não igual ao total: {custo_empresa_d} + {desconto_prof_d} ≠ {valor_total_d}")
                        erros += 1
        
        if erros > 0:
            self.logger.warning(f"⚠️ {erros} problemas com cálculos")
            return False
        
        self.logger.info("✅ Cálculos validados")
        return True
    
    def _validar_totais(self, dados: DadosEntrada) -> bool:
        """Validação: TOTAIS - consistência geral dos dados."""
        erros = 0
        
        # Validação de totais gerais
        total_colaboradores = len(dados.colaboradores_ativos)
        colaboradores_validos = sum(1 for c in dados.colaboradores_ativos if c.get('elegivel', True))
        colaboradores_excluidos = total_colaboradores - colaboradores_validos
        
        # Validação de consistência
        if total_colaboradores != colaboradores_validos + colaboradores_excluidos:
            self.adicionar_erro("Inconsistência no total de colaboradores")
            erros += 1
        
        # Validação de dados obrigatórios (dinâmica, com 'nome' como warning)
        obrigatorios = getattr(self.settings, 'VALIDACOES_OBRIGATORIAS', ['matricula','nome','sindicato'])
        for colaborador in dados.colaboradores_ativos:
            for campo in obrigatorios:
                if not colaborador.get(campo):
                    if campo == 'nome':
                        self.adicionar_warning(f"Campo opcional '{campo}' ausente: {colaborador.get('matricula', 'N/A')}")
                    else:
                        self.adicionar_erro(f"Campo obrigatório '{campo}' ausente: {colaborador.get('matricula', 'N/A')}")
                        erros += 1
        
        if erros > 0:
            self.logger.warning(f"⚠️ {erros} problemas com totais")
            return False
        
        self.logger.info("✅ Totais validados")
        return True
    
    def _validar_afastados(self, dados: DadosEntrada) -> List[str]:
        """Valida afastados."""
        erros = []
        for colaborador in dados.colaboradores_ativos:
            matricula = colaborador.get('matricula')
            if matricula in dados.colaboradores_afastados:
                if colaborador.get('elegivel', True):
                    erros.append(f"Colaborador {matricula} está afastado")
        return erros
    
    def _validar_desligados_geral(self, dados: DadosEntrada) -> bool:
        """Validação: DESLIGADOS GERAL."""
        erros = 0
        
        for colaborador in dados.colaboradores_ativos:
            if not colaborador.get('ativo', True):
                if colaborador.get('elegivel', True):
                    self.adicionar_erro(f"Colaborador desligado deveria ser inelegível: {colaborador.get('matricula')}")
                    erros += 1
        
        if erros > 0:
            self.logger.warning(f"⚠️ {erros} problemas com desligados")
            return False
        
        self.logger.info("✅ Desligados validados")
        return True
    
    def _validar_admitidos_mes(self, dados: DadosEntrada) -> bool:
        """Validação: Admitidos mês."""
        erros = 0
        
        for colaborador in dados.colaboradores_ativos:
            data_admissao = colaborador.get('data_admissao')
            if data_admissao:
                try:
                    # Verifica se é admissão no mês atual
                    mes_atual = datetime.now().month
                    mes_admissao = data_admissao.month if hasattr(data_admissao, 'month') else mes_atual
                    
                    if mes_admissao == mes_atual:
                        # Admitido no mês - verificar se tem dias trabalhados corretos
                        dias_trabalhados = colaborador.get('dias_trabalhados', 0)
                        if dias_trabalhados <= 0:
                            self.adicionar_erro(f"Admitido no mês sem dias trabalhados: {colaborador.get('matricula')}")
                            erros += 1
                except:
                    pass
        
        if erros > 0:
            self.logger.warning(f"⚠️ {erros} problemas com admitidos")
            return False
        
        self.logger.info("✅ Admitidos validados")
        return True
    
    def _validar_ferias(self, dados: DadosEntrada) -> bool:
        """Validação: FÉRIAS - parcial ou integral por regra de sindicato."""
        erros = 0
        
        for colaborador in dados.colaboradores_ativos:
            matricula = colaborador.get('matricula', '')
            sindicato = colaborador.get('sindicato', '')
            em_ferias = colaborador.get('em_ferias', False)
            dias_trabalhados = colaborador.get('dias_trabalhados', 0)
            
            if em_ferias:
                # Verifica se o sindicato tem regras de férias configuradas
                if sindicato in self.settings.CONFIGURACAO_SINDICATOS:
                    config_sindicato = self.settings.CONFIGURACAO_SINDICATOS[sindicato]
                    regras_ferias = config_sindicato.get('regras_ferias', {})
                    
                    if regras_ferias:
                        tipo_ferias = regras_ferias.get('tipo', 'parcial')
                        dias_minimos = regras_ferias.get('dias_minimos', 0)
                        dias_maximos = regras_ferias.get('dias_maximos', 30)
                        regra_especial = regras_ferias.get('regra_especial', '')
                        
                        # Validação baseada no tipo de férias do sindicato
                        if tipo_ferias == 'integral':
                            # Férias devem ser gozadas integralmente
                            if dias_trabalhados > 0:
                                self.adicionar_erro(
                                    f"Férias integrais não permitem dias trabalhados: {matricula} - {sindicato}"
                                )
                                erros += 1
                            
                            # Marca como não elegível para benefícios
                            colaborador['elegivel'] = False
                            colaborador['dias_trabalhados'] = 0
                            
                            if 'FÉRIAS INTEGRAIS' not in colaborador.get('observacoes', '').upper():
                                colaborador['observacoes'] = f"{colaborador.get('observacoes', '')} | FÉRIAS INTEGRAIS".strip(' |')
                        
                        elif tipo_ferias == 'parcial':
                            # Férias podem ser parciais
                            if dias_trabalhados < dias_minimos:
                                self.adicionar_warning(
                                    f"Férias parciais com dias trabalhados ({dias_trabalhados}) < mínimo ({dias_minimos}): {matricula} - {sindicato}"
                                )
                                erros += 1
                            
                            if dias_trabalhados > dias_maximos:
                                self.adicionar_erro(
                                    f"Férias parciais com dias trabalhados ({dias_trabalhados}) > máximo ({dias_maximos}): {matricula} - {sindicato}"
                                )
                                erros += 1
                            
                            # Adiciona observação sobre férias parciais
                            if 'FÉRIAS PARCIAIS' not in colaborador.get('observacoes', '').upper():
                                colaborador['observacoes'] = f"{colaborador.get('observacoes', '')} | FÉRIAS PARCIAIS ({dias_trabalhados} dias)".strip(' |')
                        
                        # Adiciona regra especial do sindicato
                        if regra_especial and regra_especial not in colaborador.get('observacoes', ''):
                            colaborador['observacoes'] = f"{colaborador.get('observacoes', '')} | {regra_especial}".strip(' |')
                        
                        # Validação de elegibilidade para benefícios
                        if dias_trabalhados > 0:
                            # Colaborador em férias parciais pode receber benefícios proporcionais
                            colaborador['elegivel'] = True
                            
                            # Calcula valor proporcional baseado nos dias trabalhados usando Decimal
                            from decimal import Decimal as _D
                            valor_vr = colaborador.get('valor_vr', 0)
                            valor_vr_d = valor_vr if isinstance(valor_vr, _D) else _D(str(valor_vr))
                            valor_total = valor_vr_d * _D(int(dias_trabalhados))
                            colaborador['valor_total_beneficio'] = valor_total
                            
                            # Aplica percentuais da empresa como Decimal
                            percentual_empresa = _D(str(config_sindicato.get('percentual_empresa', 0.80)))
                            percentual_profissional = _D(str(config_sindicato.get('percentual_profissional', 0.20)))
                            colaborador['custo_empresa'] = valor_total * percentual_empresa
                            colaborador['desconto_profissional'] = valor_total * percentual_profissional
                        else:
                            # Colaborador em férias integrais não recebe benefícios
                            colaborador['elegivel'] = False
                            colaborador['valor_total_beneficio'] = 0
                            colaborador['custo_empresa'] = 0
                            colaborador['desconto_profissional'] = 0
                    
                    else:
                        self.adicionar_warning(f"Sindicato {sindicato} sem regras de férias configuradas: {matricula}")
                        erros += 1
                else:
                    # Nossos dados usam estados; não tratar ausência em CONFIGURACAO_SINDICATOS como erro
                    self.adicionar_warning(f"Sindicato {sindicato} não encontrado na configuração: {matricula}")
                    # não incrementa 'erros' aqui
        
        # Adiciona observação sobre férias processadas
        total_ferias = sum(1 for c in dados.colaboradores_ativos if c.get('em_ferias', False))
        ferias_integrais = sum(1 for c in dados.colaboradores_ativos 
                              if c.get('em_ferias', False) and 
                              c.get('sindicato') in self.settings.CONFIGURACAO_SINDICATOS and
                              self.settings.CONFIGURACAO_SINDICATOS[c.get('sindicato')].get('regras_ferias', {}).get('tipo') == 'integral')
        ferias_parciais = total_ferias - ferias_integrais
        
        dados.adicionar_observacao_geral(f"Férias processadas: {total_ferias} total ({ferias_integrais} integrais, {ferias_parciais} parciais)")
        
        if erros > 0:
            self.logger.warning(f"⚠️ {erros} problemas com férias")
            return False
        
        self.logger.info("✅ Férias validadas por regras de sindicato")
        return True
    
    def _validar_estagio(self, dados: DadosEntrada) -> List[str]:
        """Valida estagiários."""
        erros = []
        for colaborador in dados.colaboradores_ativos:
            matricula = colaborador.get('matricula')
            if matricula in dados.colaboradores_estagio:
                if colaborador.get('elegivel', True):
                    erros.append(f"Colaborador {matricula} é estagiário")
        return erros
    
    def _validar_aprendiz(self, dados: DadosEntrada) -> List[str]:
        """Valida aprendizes."""
        erros = []
        for colaborador in dados.colaboradores_ativos:
            matricula = colaborador.get('matricula')
            if matricula in dados.colaboradores_aprendiz:
                if colaborador.get('elegivel', True):
                    erros.append(f"Colaborador {matricula} é aprendiz")
        return erros
    
    def _validar_desligamento_dia_15(self, dados: DadosEntrada) -> bool:
        """Validação: DESLIGADOS ATÉ O DIA 15 - EXCLUIR DA COMPRA."""
        erros = 0
        
        for colaborador in dados.colaboradores_ativos:
            if not colaborador.get('ativo', True):
                data_desligamento = colaborador.get('data_desligamento')
                if data_desligamento:
                    try:
                        dia = data_desligamento.day if hasattr(data_desligamento, 'day') else 15
                        
                        if dia <= self.settings.DIA_LIMITE_DESLIGAMENTO:
                            # Desligado até dia 15 - deve ser inelegível
                            if colaborador.get('elegivel', True):
                                self.adicionar_erro(f"Desligado até dia 15 deveria ser inelegível: {colaborador.get('matricula')}")
                                erros += 1
                            
                            if colaborador.get('dias_trabalhados', 0) > 0:
                                self.adicionar_erro(f"Desligado até dia 15 com dias trabalhados: {colaborador.get('matricula')}")
                                erros += 1
                    except:
                        pass
        
        if erros > 0:
            self.logger.warning(f"⚠️ {erros} problemas com desligamento até dia 15")
            return False
        
        self.logger.info("✅ Desligamento até dia 15 validado")
        return True
    
    def _validar_desligamento_dia_16_plus(self, dados: DadosEntrada) -> bool:
        """Validação: DESLIGADOS DO DIA 16+ - RECARGA CHEIA, DESCONTO PROPORCIONAL."""
        erros = 0
        
        for colaborador in dados.colaboradores_ativos:
            if not colaborador.get('ativo', True):
                data_desligamento = colaborador.get('data_desligamento')
                if data_desligamento:
                    try:
                        dia = data_desligamento.day if hasattr(data_desligamento, 'day') else 15
                        
                        if dia > self.settings.DIA_LIMITE_DESLIGAMENTO:
                            # Desligado após dia 15 - deve ser elegível proporcionalmente
                            if not colaborador.get('elegivel', False):
                                self.adicionar_erro(f"Desligado após dia 15 deveria ser elegível: {colaborador.get('matricula')}")
                                erros += 1
                            
                            dias_trabalhados = colaborador.get('dias_trabalhados', 0)
                            if dias_trabalhados <= 0:
                                self.adicionar_erro(f"Desligado após dia 15 sem dias trabalhados: {colaborador.get('matricula')}")
                                erros += 1
                    except:
                        pass
        
        if erros > 0:
            self.logger.warning(f"⚠️ {erros} problemas com desligamento após dia 15")
            return False
        
        self.logger.info("✅ Desligamento após dia 15 validado")
        return True
    
    def _validar_exterior(self, dados: DadosEntrada) -> List[str]:
        """Valida colaboradores no exterior."""
        erros = []
        for colaborador in dados.colaboradores_ativos:
            matricula = colaborador.get('matricula')
            if matricula in dados.colaboradores_exterior:
                if colaborador.get('elegivel', True):
                    erros.append(f"Colaborador {matricula} está no exterior")
        return erros
    
    def _validar_feriados(self, dados: DadosEntrada) -> bool:
        """Validação: FERIADOS - estaduais e municipais corretamente aplicados."""
        erros = 0
        
        # Obtém configuração de feriados
        feriados_nacionais = self.settings.FERIADOS_MAIO_2025
        feriados_estaduais = self.settings.FERIADOS_ESTADUAIS
        feriados_municipais = self.settings.FERIADOS_MUNICIPAIS
        
        for colaborador in dados.colaboradores_ativos:
            matricula = colaborador.get('matricula', '')
            sindicato = colaborador.get('sindicato', '')
            dias_trabalhados = colaborador.get('dias_trabalhados', 0)
            
            # Determina estado/município baseado no sindicato (exemplo)
            estado = self._determinar_estado_por_sindicato(sindicato)
            municipio = self._determinar_municipio_por_sindicato(sindicato)
            
            # Calcula dias úteis considerando feriados
            dias_uteis_esperados = self._calcular_dias_uteis_com_feriados(
                estado, municipio, feriados_nacionais, feriados_estaduais, feriados_municipais
            )
            
            # Verifica se os dias trabalhados estão corretos
            if dias_trabalhados > dias_uteis_esperados:
                self.adicionar_warning(
                    f"Dias trabalhados ({dias_trabalhados}) > dias úteis ({dias_uteis_esperados}): {matricula}"
                )
                erros += 1
            
            # Verifica se feriados estão sendo considerados
            if dias_trabalhados == 31:  # Mês completo sem considerar feriados
                self.adicionar_warning(
                    f"Possível erro: mês completo sem considerar feriados: {matricula}"
                )
        
        # Adiciona observação sobre feriados
        total_feriados = len(feriados_nacionais)
        dados.adicionar_observacao_geral(f"Feriados considerados: {total_feriados} (nacionais)")
        
        if erros > 0:
            self.logger.warning(f"⚠️ {erros} problemas com feriados")
            return False
        
        self.logger.info("✅ Feriados validados")
        return True
    
    def _determinar_estado_por_sindicato(self, sindicato: str) -> str:
        """Determina estado baseado no nome do sindicato."""
        sindicato_upper = sindicato.upper()
        
        if 'SP' in sindicato_upper or 'SAO PAULO' in sindicato_upper:
            return "SP"
        elif 'RJ' in sindicato_upper or 'RIO' in sindicato_upper:
            return "RJ"
        elif 'MG' in sindicato_upper or 'MINAS' in sindicato_upper:
            return "MG"
        else:
            return "SP"  # Padrão
    
    def _determinar_municipio_por_sindicato(self, sindicato: str) -> str:
        """Determina município baseado no nome do sindicato."""
        sindicato_upper = sindicato.upper()
        
        if 'SP' in sindicato_upper or 'SAO PAULO' in sindicato_upper:
            return "SAO_PAULO"
        elif 'RJ' in sindicato_upper or 'RIO' in sindicato_upper:
            return "RIO_JANEIRO"
        elif 'MG' in sindicato_upper or 'BELO HORIZONTE' in sindicato_upper:
            return "BELO_HORIZONTE"
        else:
            return "SAO_PAULO"  # Padrão
    
    def _calcular_dias_uteis_com_feriados(self, estado: str, municipio: str, 
                                         feriados_nacionais: List[int], 
                                         feriados_estaduais: Dict[str, List[int]], 
                                         feriados_municipais: Dict[str, List[int]]) -> int:
        """Calcula dias úteis considerando feriados."""
        # Total de dias no mês (maio = 31)
        total_dias = 31
        
        # Dias de fim de semana (sábados e domingos)
        # Maio/2025: 4 sábados + 4 domingos = 8 dias
        dias_fim_semana = 8
        
        # Feriados nacionais
        dias_feriados_nacionais = len(feriados_nacionais)
        
        # Feriados estaduais (excluindo nacionais)
        feriados_estado = feriados_estaduais.get(estado, [])
        dias_feriados_estado = len([f for f in feriados_estado if f not in feriados_nacionais])
        
        # Feriados municipais (excluindo nacionais e estaduais)
        feriados_municipio = feriados_municipais.get(municipio, [])
        dias_feriados_municipio = len([f for f in feriados_municipio 
                                      if f not in feriados_nacionais and f not in feriados_estado])
        
        # Total de dias úteis
        dias_uteis = total_dias - dias_fim_semana - dias_feriados_nacionais - dias_feriados_estado - dias_feriados_municipio
        
        return max(dias_uteis, 0)  # Não pode ser negativo

    def _validar_folha_ponto(self, dados: DadosEntrada) -> bool:
        """Validação: FOLHA PONTO - consistência com dados reais."""
        erros = 0
        
        # Configuração de feriados para maio/2025
        feriados_nacionais = self.settings.FERIADOS_MAIO_2025
        total_dias_mes = 31
        dias_fim_semana = 8  # Maio/2025: 4 sábados + 4 domingos
        dias_feriados = len(feriados_nacionais)
        dias_uteis_esperados_default = total_dias_mes - dias_fim_semana - dias_feriados
        
        expected_set = []
        
        for colaborador in dados.colaboradores_ativos:
            matricula = colaborador.get('matricula', '')
            dias_trabalhados = colaborador.get('dias_trabalhados', 0)
            dias_uteis = colaborador.get('dias_uteis', 0)
            sindicato = colaborador.get('sindicato', '')
            cargo = colaborador.get('cargo', '')
            
            # Dias úteis esperados: usa do colaborador > planilha por sindicato > default calculado
            dias_uteis_planilha = dados.dias_uteis_por_sindicato.get(sindicato)
            dias_uteis_esperados = dias_uteis or dias_uteis_planilha or dias_uteis_esperados_default
            try:
                dias_uteis_esperados = int(dias_uteis_esperados)
            except Exception:
                dias_uteis_esperados = dias_uteis_esperados_default
            expected_set.append(dias_uteis_esperados)
            
            # 1. Validação de dias trabalhados vs dias úteis esperados
            if dias_trabalhados > dias_uteis_esperados:
                self.adicionar_warning(
                    f"Dias trabalhados ({dias_trabalhados}) > dias úteis esperados ({dias_uteis_esperados}): {matricula}"
                )
                erros += 1
            
            # 2. Validação de dias úteis por sindicato (já usando planilha acima)
            dias_uteis_sindicato = dados.dias_uteis_por_sindicato.get(sindicato)
            if dias_uteis_sindicato is None and sindicato in self.settings.CONFIGURACAO_SINDICATOS:
                dias_uteis_sindicato = self.settings.CONFIGURACAO_SINDICATOS[sindicato].get('dias_uteis_mes', dias_uteis_esperados_default)
            if dias_uteis_sindicato is not None and dias_uteis and dias_uteis != dias_uteis_sindicato:
                self.adicionar_warning(
                    f"Dias úteis ({dias_uteis}) ≠ dias (planilha) ({dias_uteis_sindicato}): {matricula}"
                )
                erros += 1
            
            # 3. Validação de consistência com férias
            if colaborador.get('em_ferias', False):
                if dias_trabalhados > 0:
                    self.adicionar_erro(
                        f"Colaborador em férias com dias trabalhados > 0: {matricula}"
                    )
                    erros += 1
            
            # 4. Validação de consistência com desligamento
            if colaborador.get('data_desligamento'):
                # Verifica se dias trabalhados fazem sentido com data de desligamento
                dia_desligamento = colaborador.get('data_desligamento')
                if hasattr(dia_desligamento, 'day'):
                    dia = dia_desligamento.day
                    if dia <= 15 and dias_trabalhados > 0:
                        self.adicionar_warning(
                            f"Desligado até dia 15 com dias trabalhados > 0: {matricula}"
                        )
                        erros += 1
            
            # 5. Validação de dias parciais
            if 0 < dias_trabalhados < 15:
                # Verifica se tem observação sobre dias parciais
                observacoes = colaborador.get('observacoes', '')
                if 'DIAS PARCIAIS' not in observacoes.upper():
                    colaborador['observacoes'] = f"{observacoes} | DIAS PARCIAIS".strip(' |')
            
            # 6. Validação de mês completo
            if dias_trabalhados == dias_uteis_esperados:
                # Verifica se não há inconsistências
                if colaborador.get('em_ferias', False):
                    self.adicionar_warning(
                        f"Colaborador em férias com mês completo: {matricula}"
                    )
                    erros += 1
        
        # Observação com base real (estatística de dias esperados únicos)
        try:
            resumo = sorted(set(int(x) for x in expected_set if x is not None))
            dados.adicionar_observacao_geral(f"Folha ponto validada: dias úteis esperados {resumo}")
        except Exception:
            dados.adicionar_observacao_geral(f"Folha ponto validada: {dias_uteis_esperados_default} dias úteis esperados")
        
        if erros > 0:
            self.logger.warning(f"⚠️ {erros} problemas com folha ponto")
            return False
        
        self.logger.info("✅ Folha ponto validada")
        return True 

    def _validar_diretores(self, dados: DadosEntrada) -> bool:
        """Validação: Diretores - devem ser excluídos do benefício."""
        erros = 0
        
        # Cargos de diretores (case-insensitive)
        cargos_diretores = [
            'diretor',
            'diretor geral',
            'diretor executivo',
            'diretor administrativo',
            'diretor financeiro',
            'diretor comercial',
            'diretor de operações',
            'diretor de rh',
            'diretor de ti',
            'presidente',
            'vice-presidente',
            'ceo',
            'cfo',
            'cto',
            'coo',
            'coordenador'  # tratado como inelegível junto com diretores
        ]
        
        for colaborador in dados.colaboradores_ativos:
            cargo = colaborador.get('cargo', '').lower()
            matricula = colaborador.get('matricula', '')
            
            # Verifica se é diretor
            if any(cargo_diretor in cargo for cargo_diretor in cargos_diretores):
                if colaborador.get('elegivel', True):
                    self.adicionar_erro(
                        f"Diretor deveria ser inelegível: {matricula} - cargo: {colaborador.get('cargo', '')}"
                    )
                    erros += 1
                
                # Marca como diretor para exclusão
                colaborador['elegivel'] = False
                colaborador['dias_trabalhados'] = 0
                colaborador['motivo_exclusao'] = 'DIRETOR'
                
                # Adiciona à lista de exclusões
                dados.adicionar_exclusao_afastado(matricula)
        
        # Adiciona observação sobre diretores
        diretores_encontrados = sum(
            1 for c in dados.colaboradores_ativos 
            if any(cargo_diretor in c.get('cargo', '').lower() for cargo_diretor in cargos_diretores)
        )
        dados.adicionar_observacao_geral(f"Diretores encontrados e excluídos: {diretores_encontrados}")
        
        if erros > 0:
            self.logger.warning(f"⚠️ {erros} problemas com diretores")
            return False
        
        self.logger.info("✅ Diretores validados")
        return True 

    def _validar_calculo_pagamento(self, dados: DadosEntrada) -> bool:
        """Validação: CÁLCULO DE PAGAMENTO - regra 80% empresa + 20% profissional."""
        erros = 0
        
        for colaborador in dados.colaboradores_ativos:
            if colaborador.get('elegivel', True):
                valor_total = colaborador.get('valor_total_beneficio', 0)
                custo_empresa = colaborador.get('custo_empresa', 0)
                desconto_profissional = colaborador.get('desconto_profissional', 0)
                
                from decimal import Decimal as _D
                try:
                    valor_total_d = valor_total if isinstance(valor_total, _D) else _D(str(valor_total))
                    custo_empresa_d = custo_empresa if isinstance(custo_empresa, _D) else _D(str(custo_empresa))
                    desconto_prof_d = desconto_profissional if isinstance(desconto_profissional, _D) else _D(str(desconto_profissional))
                except Exception:
                    continue
                
                if valor_total_d > 0:
                    # Verifica se os percentuais somam 100%
                    percentual_empresa = custo_empresa_d / valor_total_d
                    percentual_profissional = desconto_prof_d / valor_total_d
                    if abs(percentual_empresa + percentual_profissional - _D('1.0')) > _D('0.01'):
                        self.adicionar_erro(f"Percentuais não somam 100%: {percentual_empresa:.2%} + {percentual_profissional:.2%} ≠ 100%")
                        erros += 1
        
        if erros > 0:
            self.logger.warning(f"⚠️ {erros} problemas com cálculo de pagamento")
            return False
        
        self.logger.info("✅ Cálculo de pagamento validado")
        return True 

    def _validar_admitidos_mes_anterior(self, dados: DadosEntrada) -> bool:
        """Validação: Admitidos mês anterior (abril)."""
        erros = 0
        
        for colaborador in dados.colaboradores_ativos:
            data_admissao = colaborador.get('data_admissao')
            if data_admissao:
                try:
                    # Verifica se é admissão no mês anterior (abril = 4)
                    mes_atual = datetime.now().month
                    mes_admissao = data_admissao.month if hasattr(data_admissao, 'month') else mes_atual
                    
                    if mes_admissao == 4:  # Abril
                        # Admitido em abril - verificar se tem dias trabalhados corretos
                        dias_trabalhados = colaborador.get('dias_trabalhados', 0)
                        
                        if dias_trabalhados <= 0:
                            self.adicionar_erro(
                                f"Admitido em abril sem dias trabalhados: {colaborador.get('matricula')}"
                            )
                            erros += 1
                        
                        # Verifica se tem observação sobre admissão
                        if not colaborador.get('observacoes', ''):
                            colaborador['observacoes'] = 'ADMITIDO EM ABRIL'
                        
                        # Marca como admitido mês anterior
                        colaborador['admitido_mes_anterior'] = True
                        
                        # Verifica se tem data de admissão válida
                        if hasattr(data_admissao, 'year'):
                            ano_admissao = data_admissao.year
                            if ano_admissao != 2025:
                                self.adicionar_warning(
                                    f"Admitido em abril de ano diferente: {colaborador.get('matricula')} - {ano_admissao}"
                                )
                
                except Exception as e:
                    self.logger.warning(f"Erro ao validar admissão abril: {e}")
        
        # Adiciona observação sobre admitidos abril
        admitidos_abril = sum(
            1 for c in dados.colaboradores_ativos 
            if c.get('admitido_mes_anterior', False)
        )
        dados.adicionar_observacao_geral(f"Admitidos em abril: {admitidos_abril}")
        
        if erros > 0:
            self.logger.warning(f"⚠️ {erros} problemas com admitidos abril")
            return False
        
        self.logger.info("✅ Admitidos mês anterior validados")
        return True 

    def _validar_atendimentos_obs(self, dados: DadosEntrada) -> bool:
        """Validação: ATENDIMENTOS/OBS - valida observações e atendimentos."""
        erros = 0
        
        for colaborador in dados.colaboradores_ativos:
            matricula = colaborador.get('matricula', '')
            observacoes = colaborador.get('observacoes', '')
            motivo_exclusao = colaborador.get('motivo_exclusao', '')
            
            # 1. Validação de observações obrigatórias para casos especiais
            if not colaborador.get('ativo', True):
                if not observacoes and not motivo_exclusao:
                    self.adicionar_warning(
                        f"Colaborador inativo sem observações: {matricula}"
                    )
            
            # 2. Validação de observações para férias
            if colaborador.get('em_ferias', False):
                if 'FÉRIAS' not in observacoes.upper():
                    colaborador['observacoes'] = f"{observacoes} | EM FÉRIAS".strip(' |')
            
            # 3. Validação de observações para desligados
            if colaborador.get('data_desligamento'):
                if 'DESLIGADO' not in observacoes.upper():
                    colaborador['observacoes'] = f"{observacoes} | DESLIGADO".strip(' |')
            
            # 4. Validação de observações para afastados
            situacao = colaborador.get('situacao', '').lower()
            if any(palavra in situacao for palavra in ['licença', 'afastado', 'auxílio']):
                if 'AFASTADO' not in observacoes.upper():
                    colaborador['observacoes'] = f"{observacoes} | AFASTADO".strip(' |')
            
            # 5. Validação de observações para estagiários/aprendizes
            cargo = colaborador.get('cargo', '').lower()
            if 'estagio' in cargo: # Changed from 'estagiario' to 'estagio'
                if 'ESTAGIO' not in observacoes.upper():
                    colaborador['observacoes'] = f"{observacoes} | ESTAGIO".strip(' |') # Changed from 'ESTAGIÁRIO' to 'ESTAGIO'
            elif 'aprendiz' in cargo:
                if 'APRENDIZ' not in observacoes.upper():
                    colaborador['observacoes'] = f"{observacoes} | APRENDIZ".strip(' |')
            
            # 6. Validação de observações para diretores
            if any(cargo_diretor in cargo for cargo_diretor in ['diretor', 'presidente', 'ceo', 'cfo', 'cto', 'coo']):
                if 'DIRETOR' not in observacoes.upper():
                    colaborador['observacoes'] = f"{observacoes} | DIRETOR".strip(' |')
            
            # 7. Validação de observações para admitidos
            if colaborador.get('admitido_mes_anterior', False):
                if 'ABRIL' not in observacoes.upper():
                    colaborador['observacoes'] = f"{observacoes} | ADMITIDO EM ABRIL".strip(' |')
            
            # 8. Validação de observações para dias parciais
            dias_trabalhados = colaborador.get('dias_trabalhados', 0)
            if 0 < dias_trabalhados < 15:
                if 'DIAS PARCIAIS' not in observacoes.upper():
                    colaborador['observacoes'] = f"{observacoes} | DIAS PARCIAIS".strip(' |')
            
            # 9. Validação de observações para valores zero
            valor_total = colaborador.get('valor_total_beneficio', 0)
            if valor_total == 0 and colaborador.get('elegivel', True):
                if 'VALOR ZERO' not in observacoes.upper():
                    colaborador['observacoes'] = f"{observacoes} | VALOR ZERO".strip(' |')
            
            # 10. Validação de observações para sem sindicato
            sindicato = colaborador.get('sindicato', '')
            if not sindicato:
                if 'SEM SINDICATO' not in observacoes.upper():
                    colaborador['observacoes'] = f"{observacoes} | SEM SINDICATO".strip(' |')
        
        # Adiciona observação sobre atendimentos/OBS
        total_obs = sum(1 for c in dados.colaboradores_ativos if c.get('observacoes', ''))
        dados.adicionar_observacao_geral(f"Atendimentos/OBS processados: {total_obs}/{len(dados.colaboradores_ativos)}")
        
        if erros > 0:
            self.logger.warning(f"⚠️ {erros} problemas com atendimentos/OBS")
            return False
        
        self.logger.info("✅ Atendimentos/OBS validados")
        return True 

    def _validar_datas_quebradas(self, dados: DadosEntrada) -> bool:
        """Validação: DATAS QUEBRADAS - admissões e desligamentos no meio do mês."""
        erros = 0
        
        for colaborador in dados.colaboradores_ativos:
            matricula = colaborador.get('matricula', '')
            data_admissao = colaborador.get('data_admissao')
            data_desligamento = colaborador.get('data_desligamento')
            dias_trabalhados = colaborador.get('dias_trabalhados', 0)
            sindicato = colaborador.get('sindicato', '')
            
            # 1. Validação de admissão no meio do mês
            if data_admissao:
                try:
                    if hasattr(data_admissao, 'day'):
                        dia_admissao = data_admissao.day
                        
                        # Se admitido após o dia 1, deve ter dias trabalhados proporcionais
                        if dia_admissao > 1:
                            dias_esperados = 31 - dia_admissao + 1  # +1 para incluir o dia da admissão
                            
                            if dias_trabalhados > dias_esperados:
                                self.adicionar_warning(
                                    f"Admissão dia {dia_admissao} com dias trabalhados ({dias_trabalhados}) > esperado ({dias_esperados}): {matricula}"
                                )
                                erros += 1
                            
                            # Adiciona observação sobre admissão parcial
                            if 'ADMISSÃO PARCIAL' not in colaborador.get('observacoes', '').upper():
                                colaborador['observacoes'] = f"{colaborador.get('observacoes', '')} | ADMISSÃO DIA {dia_admissao}".strip(' |')
                            
                            # Verifica se está seguindo regra do sindicato
                            if sindicato in self.settings.CONFIGURACAO_SINDICATOS:
                                config_sindicato = self.settings.CONFIGURACAO_SINDICATOS[sindicato]
                                regras = config_sindicato.get('regras_especiais', [])
                                
                                if 'Admissão proporcional' not in regras:
                                    self.adicionar_warning(
                                        f"Sindicato {sindicato} sem regra de admissão proporcional: {matricula}"
                                    )
                
                except Exception as e:
                    self.logger.warning(f"Erro ao validar data admissão: {e}")
            
            # 2. Validação de desligamento no meio do mês
            if data_desligamento:
                try:
                    if hasattr(data_desligamento, 'day'):
                        dia_desligamento = data_desligamento.day
                        
                        # Regra específica: até dia 15 não considerar, após dia 15 proporcional
                        if dia_desligamento <= 15:
                            if dias_trabalhados > 0:
                                self.adicionar_warning(
                                    f"Desligado dia {dia_desligamento} (≤15) com dias trabalhados > 0: {matricula}"
                                )
                                erros += 1
                            
                            # Marca como não elegível
                            colaborador['elegivel'] = False
                            colaborador['dias_trabalhados'] = 0
                            
                            if 'DESLIGADO ATÉ DIA 15' not in colaborador.get('observacoes', '').upper():
                                colaborador['observacoes'] = f"{colaborador.get('observacoes', '')} | DESLIGADO ATÉ DIA 15".strip(' |')
                        
                        else:  # Desligamento após dia 15
                            dias_esperados = dia_desligamento
                            
                            if dias_trabalhados > dias_esperados:
                                self.adicionar_warning(
                                    f"Desligado dia {dia_desligamento} com dias trabalhados ({dias_trabalhados}) > esperado ({dias_esperados}): {matricula}"
                                )
                                erros += 1
                            
                            # Adiciona observação sobre desligamento parcial
                            if 'DESLIGAMENTO PARCIAL' not in colaborador.get('observacoes', '').upper():
                                colaborador['observacoes'] = f"{colaborador.get('observacoes', '')} | DESLIGAMENTO DIA {dia_desligamento}".strip(' |')
                            
                            # Verifica se está seguindo regra do sindicato
                            if sindicato in self.settings.CONFIGURACAO_SINDICATOS:
                                config_sindicato = self.settings.CONFIGURACAO_SINDICATOS[sindicato]
                                regras = config_sindicato.get('regras_especiais', [])
                                
                                if 'Desligamento proporcional' not in regras:
                                    self.adicionar_warning(
                                        f"Sindicato {sindicato} sem regra de desligamento proporcional: {matricula}"
                                    )
                
                except Exception as e:
                    self.logger.warning(f"Erro ao validar data desligamento: {e}")
            
            # 3. Validação de inconsistências entre admissão e desligamento
            if data_admissao and data_desligamento:
                try:
                    if hasattr(data_admissao, 'month') and hasattr(data_desligamento, 'month'):
                        if data_admissao.month == data_desligamento.month:
                            self.adicionar_warning(
                                f"Admissão e desligamento no mesmo mês: {matricula}"
                            )
                            erros += 1
                
                except Exception as e:
                    self.logger.warning(f"Erro ao validar inconsistência: {e}")
        
        # Adiciona observação sobre datas quebradas
        total_datas_quebradas = sum(
            1 for c in dados.colaboradores_ativos 
            if ('ADMISSÃO PARCIAL' in c.get('observacoes', '') or 
                'DESLIGAMENTO PARCIAL' in c.get('observacoes', ''))
        )
        dados.adicionar_observacao_geral(f"Datas quebradas processadas: {total_datas_quebradas}")
        
        if erros > 0:
            self.logger.warning(f"⚠️ {erros} problemas com datas quebradas")
            return False
        
        self.logger.info("✅ Datas quebradas validadas")
        return True 

    def _validar_acordos_coletivos(self, dados: DadosEntrada) -> List[str]:
        """Validação: ACORDOS COLETIVOS - regras vigentes de cada sindicato."""
        warnings = []
        for colaborador in dados.colaboradores_ativos:
            sindicato = colaborador.get('sindicato', '')
            if sindicato not in dados.config_sindicatos:
                warnings.append(f"Sindicato {sindicato} não configurado para {colaborador.get('matricula')}")
        return warnings

    def _validar_feriados(self, dados: DadosEntrada) -> bool:
        """Validação: FERIADOS - estaduais e municipais corretamente aplicados."""
        erros = 0
        
        # Obtém configuração de feriados
        feriados_nacionais = self.settings.FERIADOS_MAIO_2025
        feriados_estaduais = self.settings.FERIADOS_ESTADUAIS
        feriados_municipais = self.settings.FERIADOS_MUNICIPAIS
        
        for colaborador in dados.colaboradores_ativos:
            matricula = colaborador.get('matricula', '')
            sindicato = colaborador.get('sindicato', '')
            dias_trabalhados = colaborador.get('dias_trabalhados', 0)
            
            # Determina estado/município baseado no sindicato (exemplo)
            estado = self._determinar_estado_por_sindicato(sindicato)
            municipio = self._determinar_municipio_por_sindicato(sindicato)
            
            # Calcula dias úteis considerando feriados
            dias_uteis_esperados = self._calcular_dias_uteis_com_feriados(
                estado, municipio, feriados_nacionais, feriados_estaduais, feriados_municipais
            )
            
            # Verifica se os dias trabalhados estão corretos
            if dias_trabalhados > dias_uteis_esperados:
                self.adicionar_warning(
                    f"Dias trabalhados ({dias_trabalhados}) > dias úteis ({dias_uteis_esperados}): {matricula}"
                )
                erros += 1
            
            # Verifica se feriados estão sendo considerados
            if dias_trabalhados == 31:  # Mês completo sem considerar feriados
                self.adicionar_warning(
                    f"Possível erro: mês completo sem considerar feriados: {matricula}"
                )
        
        # Adiciona observação sobre feriados
        total_feriados = len(feriados_nacionais)
        dados.adicionar_observacao_geral(f"Feriados considerados: {total_feriados} (nacionais)")
        
        if erros > 0:
            self.logger.warning(f"⚠️ {erros} problemas com feriados")
            return False
        
        self.logger.info("✅ Feriados validados")
        return True 