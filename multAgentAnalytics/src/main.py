#!/usr/bin/env python3
"""
Sistema Multiagente VR/VA - Versão Simplificada
===============================================
Executa processamento e gera CSV + prints
"""

import asyncio
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent))

from agents.coordenador import AgenteCoordenador
from config.settings import Settings

async def main():
    """Função principal simplificada."""
    print("🚀 Sistema Multiagente VR/VA - Iniciando...")
    
    # Configurações
    settings = Settings()
    
    # Criar coordenador
    coordenador = AgenteCoordenador(settings)
    
    try:
        # Executar fluxo completo
        resultado = await coordenador.executar_fluxo_completo()
        
        if resultado:
            print("✅ Processamento concluído com sucesso!")
            print(f"📊 Resultados salvos em: {settings.OUTPUT_DIR}")
        else:
            print("❌ Processamento falhou!")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    # Executar
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 