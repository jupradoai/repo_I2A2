"""
Agente de Limpeza - Aplica regras de exclusão e limpeza.
"""

from typing import Any

from .base import BaseAgente
from models.dados_entrada import DadosEntrada

class AgenteLimpeza(BaseAgente):
    """Aplica exclusões baseadas nas regras de negócio."""
    
    def __init__(self, settings):
        super().__init__(settings, "Limpeza")
        
    async def _executar_agente(self, dados_entrada: DadosEntrada) -> DadosEntrada:
        """Executa exclusões e limpeza dos dados."""
        try:
            self.logger.info("🧹 Aplicando exclusões...")
            
            # Aplica todas as exclusões
            self._excluir_por_cargo(dados_entrada)
            self._excluir_por_situacao(dados_entrada)
            self._excluir_por_matricula(dados_entrada)
            self._processar_ferias(dados_entrada)  # Processa férias
            self._processar_desligamentos(dados_entrada)
            
            self.logger.info(f"✅ Limpeza concluída: {len(dados_entrada.colaboradores_ativos)} ativos restantes")
            return dados_entrada
            
        except Exception as e:
            self.logger.error(f"❌ Erro na limpeza: {e}")
            raise
    
    def _excluir_por_cargo(self, dados: DadosEntrada):
        """Exclui por cargo (ESTAGIARIO, APRENDIZ)."""
        cargos_excluidos = ['estagiario', 'aprendiz']
        removidos = []
        
        for colaborador in dados.colaboradores_ativos[:]:
            cargo = colaborador.get('cargo', '').lower()
            
            # Diretores e coordenadores: não removemos, apenas tornamos inelegíveis e anotamos
            if any(p in cargo for p in ['diretor', 'coordenador']):
                colaborador['elegivel'] = False
                colaborador['dias_trabalhados'] = 0
                colaborador['motivo_exclusao'] = 'CARGO_DIRETORIA/COORDENACAO'
                continue
            
            if any(cargo_excluido in cargo for cargo_excluido in cargos_excluidos):
                removidos.append(colaborador)
                dados.colaboradores_ativos.remove(colaborador)
                
                # Adiciona à lista apropriada
                if 'estagiario' in cargo:
                    dados.adicionar_exclusao_estagio(colaborador.get('matricula', ''))
                elif 'aprendiz' in cargo:
                    dados.adicionar_exclusao_aprendiz(colaborador.get('matricula', ''))
        
        self.logger.info(f"✅ Excluídos por cargo: {len(removidos)}")
    
    def _excluir_por_situacao(self, dados: DadosEntrada):
        """Exclui por situação (Licença Maternidade, Auxílio Doença)."""
        situacoes_excluidas = ['licença maternidade', 'auxílio doença']
        removidos = []
        
        for colaborador in dados.colaboradores_ativos[:]:
            situacao = colaborador.get('situacao', '').lower()
            
            if any(sit_excluida in situacao for sit_excluida in situacoes_excluidas):
                removidos.append(colaborador)
                dados.colaboradores_ativos.remove(colaborador)
                dados.adicionar_exclusao_afastado(colaborador.get('matricula', ''))
        
        self.logger.info(f"✅ Excluídos por situação: {len(removidos)}")
    
    def _processar_ferias(self, dados: DadosEntrada):
        """Processa colaboradores em férias."""
        for colaborador in dados.colaboradores_ativos:
            matricula = colaborador.get('matricula', '')
            
            # Busca na lista de férias
            for ferias in dados.colaboradores_ferias:
                if str(ferias.get('matricula', '')).strip() == str(matricula).strip():
                    # Marca como em férias
                    colaborador['em_ferias'] = True
                    colaborador['dias_ferias'] = ferias.get('dias_ferias', 0)
                    break
        
        self.logger.info("✅ Férias processadas")
    
    def _excluir_por_matricula(self, dados: DadosEntrada):
        """Exclui por matrículas em listas específicas."""
        # Obtém todas as matrículas que devem ser excluídas
        matriculas_excluidas = set()
        
        # Adiciona matrículas do exterior
        for matricula in dados.colaboradores_exterior:
            matriculas_excluidas.add(str(matricula))
        
        # Adiciona matrículas de estágio
        for matricula in dados.colaboradores_estagio:
            matriculas_excluidas.add(str(matricula))
        
        # Adiciona matrículas de aprendiz
        for matricula in dados.colaboradores_aprendiz:
            matriculas_excluidas.add(str(matricula))
        
        # Adiciona matrículas de afastados
        for matricula in dados.colaboradores_afastados:
            matriculas_excluidas.add(str(matricula))
        
        # Remove colaboradores com essas matrículas
        removidos = []
        for colaborador in dados.colaboradores_ativos[:]:
            matricula = str(colaborador.get('matricula', ''))
            
            if matricula in matriculas_excluidas:
                removidos.append(colaborador)
                dados.colaboradores_ativos.remove(colaborador)
        
        self.logger.info(f"✅ Excluídos por matrícula: {len(removidos)}")
    
    def _processar_desligamentos(self, dados: DadosEntrada):
        """Processa colaboradores desligados."""
        for colaborador in dados.colaboradores_ativos:
            matricula = colaborador.get('matricula', '')
            
            # Busca na lista de desligados
            for desligado in dados.colaboradores_desligados:
                if str(desligado.get('matricula', '')).strip() == str(matricula).strip():
                    # Marca como desligado
                    colaborador['ativo'] = False
                    colaborador['data_desligamento'] = desligado.get('data_demissao')
                    
                    # Aplica regra do dia 15
                    data_demissao = desligado.get('data_demissao')
                    if data_demissao:
                        try:
                            dia = data_demissao.day if hasattr(data_demissao, 'day') else 15
                            
                            if dia <= self.settings.DIA_LIMITE_DESLIGAMENTO:
                                # Desligado antes do dia 15 - não elegível
                                colaborador['elegivel'] = False
                                colaborador['dias_trabalhados'] = 0
                            else:
                                # Desligado após dia 15 - elegível proporcionalmente
                                colaborador['elegivel'] = True
                                colaborador['dias_trabalhados'] = dia - 1  # Dias trabalhados no mês
                        except:
                            # Se não conseguir extrair o dia, assume não elegível
                            colaborador['elegivel'] = False
                            colaborador['dias_trabalhados'] = 0
                    break
        
        self.logger.info("✅ Desligamentos processados") 