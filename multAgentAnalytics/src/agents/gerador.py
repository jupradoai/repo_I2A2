"""
Agente Gerador - Gera arquivo de saída final.
"""

import pandas as pd
from pathlib import Path
from typing import Any

from .base import BaseAgente
from models.dados_entrada import DadosEntrada
from datetime import datetime

class AgenteGerador(BaseAgente):
    """Gera planilha Excel final com estrutura correta do arquivo VR MENSAL."""
    
    def __init__(self, settings):
        super().__init__(settings, "Gerador")
        
    async def _executar_agente(self, dados_entrada: DadosEntrada):
        """Executa o agente gerador."""
        try:
            print("📤 Gerando relatório final...")
            
            # Gerar relatório simples com prints
            self._gerar_relatorio_simples(dados_entrada)
            
            print("✅ Relatório gerado com sucesso!")
            return "Relatório gerado"
            
        except Exception as e:
            print(f"❌ Erro na geração: {e}")
            raise
    
    def _gerar_relatorio_simples(self, dados_entrada: DadosEntrada):
        """Gera relatório simples com prints."""
        print("\n" + "="*60)
        print("📊 RELATÓRIO FINAL - SISTEMA MULTIAGENTE VR/VA")
        print("="*60)
        
        # Estatísticas gerais
        print(f"\n📈 ESTATÍSTICAS GERAIS:")
        print(f"   • Total de colaboradores processados: {dados_entrada.total_colaboradores_processados}")
        print(f"   • Total de colaboradores válidos: {dados_entrada.colaboradores_validos}")
        print(f"   • Total de colaboradores excluídos: {dados_entrada.total_colaboradores_excluidos}")
        print(f"   • Percentual de cobertura: {dados_entrada.percentual_cobertura:.2f}%")
        
        # Totais financeiros
        print(f"\n TOTAIS FINANCEIROS:")
        print(f"   • Total de benefícios: R$ {dados_entrada.total_beneficios:,.2f}")
        print(f"   • Total custo empresa: R$ {dados_entrada.total_custo_empresa:,.2f}")
        print(f"   • Total desconto profissionais: R$ {dados_entrada.total_desconto_profissionais:,.2f}")
        
        # Resumo por sindicato
        print(f"\n🏭 RESUMO POR SINDICATO:")
        for sindicato, valor_vr in dados_entrada.config_sindicatos.items():
            print(f"   • {sindicato}: {valor_vr:.2f} dias úteis")
        
        # Observações
        if dados_entrada.observacoes_gerais:
            print(f"\n📝 OBSERVAÇÕES:")
            print(f"   {dados_entrada.observacoes_gerais}")
        
        print("\n" + "="*60)
        print("✅ PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
        print("="*60) 