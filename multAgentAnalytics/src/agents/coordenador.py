"""
Agente Coordenador - Orquestra todo o sistema multiagente.
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .base import BaseAgente
from .consolidador import AgenteConsolidador
from .limpeza import AgenteLimpeza
from .calculador import AgenteCalculador
from .validador import AgenteValidador
from .gerador import AgenteGerador
from config.settings import Settings
from models.resultado import ResultadoProcessamento
from models.dados_entrada import DadosEntrada

# ✅ ALTERNATIVA: Não herdar de BaseAgente
class AgenteCoordenador:
    """Agente Coordenador - Orquestra todo o sistema multiagente."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.agentes = {}
        self.resultado = None
        self.estatisticas_agentes = {}
        self.console = Console()
        self.duracao_total = 0
        self.total_erros = 0
        # ✅ ADICIONAR: Atributos faltantes
        self.logger = logging.getLogger(__name__)
        self._inicializar_agentes()
        
    # ✅ ADICIONAR: Método abstrato obrigatório
    async def _executar_agente(self, dados_entrada: Any) -> Any:
        """Implementação do método abstrato - não usado no coordenador."""
        raise NotImplementedError("Coordenador não implementa _executar_agente diretamente")
        
    def _inicializar_agentes(self):
        """Inicializa todos os agentes do sistema."""
        self.agentes = {
            'consolidador': AgenteConsolidador(self.settings),
            'limpeza': AgenteLimpeza(self.settings),
            'calculador': AgenteCalculador(self.settings),
            'validador': AgenteValidador(self.settings),
            'gerador': AgenteGerador(self.settings)
        }
        
    async def executar_fluxo_completo(self) -> bool:
        """Executa o fluxo completo do sistema multiagente."""
        try:
            print("🚀 Iniciando fluxo completo do sistema multiagente...")
            inicio_total = time.time()
            
            # FASE 1: Consolidação
            dados_consolidados = await self._executar_fase_consolidacao()
            if not dados_consolidados:
                print("❌ Falha na consolidação")
                return False
                
            # FASE 2: Limpeza
            dados_limpos = await self._executar_fase_limpeza(dados_consolidados)
            if not dados_limpos:
                print("❌ Falha na limpeza")
                return False
                
            # FASE 3: Cálculos
            dados_calculados = await self._executar_fase_calculos(dados_limpos)
            if not dados_calculados:
                print("❌ Falha nos cálculos")
                return False
                
            # FASE 4: Validação
            dados_validados = await self._executar_fase_validacao(dados_calculados)
            if not dados_validados:
                print("❌ Falha na validação")
                return False
                
            # FASE 5: Geração
            # Define resultado para o resumo final
            self.resultado = dados_validados
            arquivo_saida = await self._executar_fase_geracao(dados_validados)
            if not arquivo_saida:
                print("❌ Falha na geração")
                return False
                
            # Resumo final
            self.duracao_total = time.time() - inicio_total
            self._exibir_resumo_final()
            
            print("✅ Processamento concluído com sucesso!")
            print(f"📊 Resultados salvos em: {self.settings.OUTPUT_DIR}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro no fluxo completo: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    async def _executar_fase_consolidacao(self):
        """Executa a fase de consolidação."""
        print("\n📊 FASE 1: Consolidação de Dados")
        inicio = time.time()
        
        agente = AgenteConsolidador(self.settings)
        dados_consolidados = await agente.executar(None)
        
        duracao = time.time() - inicio
        print(f"✅ Consolidador Concluído em {duracao:.2f}s")
        
        # ✅ ADICIONAR: Registrar estatísticas do consolidador
        self._registrar_estatisticas_agente("Consolidador", {
            'sucesso': True,
            'duracao': duracao,
            'registros_processados': len(dados_consolidados.colaboradores_ativos),
            'total_erros': 0,
            'total_warnings': 0
        })
        
        return dados_consolidados
        
    async def _executar_fase_limpeza(self, dados_consolidados: DadosEntrada):
        """Executa a fase de limpeza."""
        print("\n🧹 FASE 2: Limpeza e Exclusão de Dados")
        inicio = time.time()
        
        agente = AgenteLimpeza(self.settings)
        dados_limpos = await agente.executar(dados_consolidados)
        
        duracao = time.time() - inicio
        print(f"✅ Limpeza Concluída em {duracao:.2f}s")
        
        # ✅ ADICIONAR: Registrar estatísticas da limpeza
        self._registrar_estatisticas_agente("Limpeza", {
            'sucesso': True,
            'duracao': duracao,
            'registros_processados': len(dados_limpos.colaboradores_ativos),
            'total_erros': 0,
            'total_warnings': 0
        })
        
        return dados_limpos
        
    async def _executar_fase_calculos(self, dados_limpos: DadosEntrada):
        """Executa a fase de cálculos."""
        print("\n🧮 FASE 3: Cálculos de Benefícios")
        inicio = time.time()
        
        agente = AgenteCalculador(self.settings)
        dados_calculados = await agente.executar(dados_limpos)
        
        duracao = time.time() - inicio
        print(f"✅ Calculador Concluído em {duracao:.2f}s")
        
        # ✅ ADICIONAR: Preencher campos de estatísticas financeiras
        dados_calculados.total_beneficios = sum(c.get('valor_total_beneficio', 0) for c in dados_calculados.colaboradores_ativos)
        dados_calculados.total_custo_empresa = sum(c.get('custo_empresa', 0) for c in dados_calculados.colaboradores_ativos)
        dados_calculados.total_desconto_profissionais = sum(c.get('desconto_profissional', 0) for c in dados_calculados.colaboradores_ativos)
        
        # ✅ ADICIONAR: Registrar estatísticas do calculador
        self._registrar_estatisticas_agente("Calculador", {
            'sucesso': True,
            'duracao': duracao,
            'registros_processados': len(dados_calculados.colaboradores_ativos),
            'total_erros': 0,
            'total_warnings': 0
        })
        
        return dados_calculados
        
    async def _executar_fase_validacao(self, dados_limpos: DadosEntrada):
        """Executa a fase de validação."""
        try:
            print("\n🔍 FASE 4: Validação de Dados")
            inicio = time.time()
            
            agente = AgenteValidador(self.settings)
            resultado = await agente.executar(dados_limpos)
            
            # PREENCHER campos de estatísticas
            dados_limpos.total_colaboradores_processados = len(dados_limpos.colaboradores_ativos)
            dados_limpos.colaboradores_validos = len([c for c in dados_limpos.colaboradores_ativos if c.get('elegivel', True)])
            dados_limpos.total_colaboradores_excluidos = len(dados_limpos.obter_matriculas_excluidas())
            
            if dados_limpos.total_colaboradores_processados > 0:
                dados_limpos.percentual_cobertura = (dados_limpos.colaboradores_validos / dados_limpos.total_colaboradores_processados) * 100
            else:
                dados_limpos.percentual_cobertura = 0.0
            
            # Registrar estatísticas do validador
            self._registrar_estatisticas_agente("Validador", {
                'sucesso': resultado.get('sucesso', False),
                'duracao': time.time() - inicio,
                'registros_processados': resultado.get('registros_processados', 0),
                'total_erros': resultado.get('total_erros', 0),
                'total_warnings': resultado.get('total_warnings', 0)
            })
            
            duracao = time.time() - inicio
            print(f"✅ Validador Concluído em {duracao:.2f}s")
            
            if not resultado.get('sucesso', False):
                print(f"❌ Erro na validação: {resultado.get('erro', 'Erro desconhecido')}")
                return None
            
            return dados_limpos
        except Exception as e:
            self.logger.error(f"❌ Erro na validação: {e}")
            return None
        
    async def _executar_fase_geracao(self, dados_calculados: DadosEntrada):
        """Executa a fase de geração."""
        print("\n📤 FASE 5: Geração de Arquivo de Saída")
        inicio = time.time()
        
        agente = AgenteGerador(self.settings)
        arquivo_saida = await agente.executar(dados_calculados)
        
        duracao = time.time() - inicio
        print(f"✅ Gerador Concluído em {duracao:.2f}s")
        
        # ✅ ADICIONAR: Registrar estatísticas do gerador
        self._registrar_estatisticas_agente("Gerador", {
            'sucesso': True,
            'duracao': duracao,
            'registros_processados': len(dados_calculados.colaboradores_ativos),
            'total_erros': 0,
            'total_warnings': 0
        })
        
        return arquivo_saida
        
    def _exibir_resumo_final(self):
        """Exibe resumo final do processamento."""
        # Usar cores válidas do Rich
        self.console.print("\n📊 RESUMO FINAL DO PROCESSAMENTO", style="bold blue")
        
        # ✅ CORRIGIR: Usar dados reais em vez de valores zerados
        total_colaboradores = len(self.resultado.colaboradores_ativos) if self.resultado and hasattr(self.resultado, 'colaboradores_ativos') else 0
        colaboradores_validos = len([c for c in self.resultado.colaboradores_ativos if c.get('elegivel', True)]) if self.resultado and hasattr(self.resultado, 'colaboradores_ativos') else 0
        colaboradores_excluidos = len(self.resultado.obter_matriculas_excluidas()) if self.resultado else 0
        
        # Criar tabela com cores válidas
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Métrica", style="cyan", no_wrap=True)
        table.add_column("Valor", style="bold green")
        
        # Adicionar dados REAIS
        table.add_row("Status", "✅ Sucesso", style="bold green")
        table.add_row("Duração", f"{self.duracao_total:.2f}s", style="yellow")
        table.add_row("Total Colaboradores", str(total_colaboradores), style="blue")
        table.add_row("Colaboradores Válidos", str(colaboradores_validos), style="green")
        table.add_row("Colaboradores Excluídos", str(colaboradores_excluidos), style="red")
        table.add_row("Erros Encontrados", str(self.total_erros), style="red")
        
        self.console.print(table)
        
        # Exibir estatísticas dos agentes
        self._exibir_estatisticas_agentes()
        
    def _exibir_estatisticas_agentes(self):
        """Exibe estatísticas de execução dos agentes."""
        if not self.estatisticas_agentes:
            print("⚠️ Nenhuma estatística de agente disponível")
            return
            
        table = Table(title="📊 Estatísticas dos Agentes", show_header=True, header_style="bold magenta")
        
        # Adicionar colunas
        table.add_column("Agente", style="cyan", no_wrap=True)
        table.add_column("Status", style="bold")
        table.add_column("Duração", style="green")
        table.add_column("Registros", style="blue")
        table.add_column("Erros", style="red")
        table.add_column("Warnings", style="yellow")
        
        # Adicionar linhas com cores válidas
        for nome, stats in self.estatisticas_agentes.items():
            status = "✅" if stats.get('sucesso', False) else "❌"
            duracao = f"{stats.get('duracao', 0):.2f}s"
            registros = stats.get('registros_processados', 0)
            erros = stats.get('total_erros', 0)
            warnings = stats.get('total_warnings', 0)
            
            # Usar cores válidas do Rich
            status_style = "bold green" if stats.get('sucesso', False) else "bold red"
            
            table.add_row(
                nome,
                status,
                duracao,
                str(registros),
                str(erros),
                str(warnings),
                style=status_style
            )
        
        self.console.print(table)
        
    def _registrar_estatisticas_agente(self, nome_agente: str, estatisticas: dict):
        """Registra estatísticas de um agente."""
        self.estatisticas_agentes[nome_agente] = estatisticas
        print(f"📊 Estatísticas do {nome_agente} registradas: {estatisticas}")
        
    def reiniciar_agentes(self):
        """Reinicia todos os agentes."""
        for agente in self.agentes.values():
            agente.limpar_estado()
        self.logger.info("🔄 Todos os agentes foram reiniciados") 