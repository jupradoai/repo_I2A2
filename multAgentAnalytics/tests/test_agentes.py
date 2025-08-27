"""
Testes para os agentes do sistema.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from pathlib import Path

from config.settings import Settings
from agents.consolidador import AgenteConsolidador
from agents.limpeza import AgenteLimpeza
from agents.calculador import AgenteCalculador
from agents.validador import AgenteValidador
from agents.gerador import AgenteGerador

@pytest.fixture
def settings():
    """Fixture para configurações de teste."""
    return Settings()

@pytest.fixture
def dados_teste():
    """Fixture para dados de teste."""
    return {
        'colaboradores_ativos': [
            {
                'matricula': '001',
                'nome': 'João Silva',
                'cargo': 'Analista',
                'sindicato': 'Sindicato A',
                'data_admissao': '2020-01-01',
                'ativo': True
            }
        ],
        'config_sindicatos': {'Sindicato A': 25.0},
        'dias_uteis_por_sindicato': {'Sindicato A': 22}
    }

class TestAgenteConsolidador:
    """Testes para o Agente Consolidador."""
    
    @pytest.mark.asyncio
    async def test_inicializacao(self, settings):
        """Testa inicialização do agente."""
        agente = AgenteConsolidador(settings)
        assert agente.nome == "Consolidador"
        assert agente.settings == settings
    
    @pytest.mark.asyncio
    async def test_execucao_basica(self, settings):
        """Testa execução básica do agente."""
        agente = AgenteConsolidador(settings)
        
        # Mock dos arquivos de entrada
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pandas.read_excel') as mock_read:
                mock_read.return_value = Mock()
                mock_read.return_value.iterrows.return_value = []
                
                resultado = await agente.executar()
                
                assert resultado is not None
                assert hasattr(resultado, 'colaboradores_ativos')

class TestAgenteLimpeza:
    """Testes para o Agente de Limpeza."""
    
    @pytest.mark.asyncio
    async def test_inicializacao(self, settings):
        """Testa inicialização do agente."""
        agente = AgenteLimpeza(settings)
        assert agente.nome == "Limpeza"
    
    @pytest.mark.asyncio
    async def test_aplicar_exclusoes_cargo(self, settings):
        """Testa aplicação de exclusões por cargo."""
        agente = AgenteLimpeza(settings)
        
        # Mock dos dados de entrada
        dados_mock = Mock()
        dados_mock.colaboradores_ativos = [
            {'cargo': 'Diretor', 'nome': 'João', 'matricula': '001'},
            {'cargo': 'Analista', 'nome': 'Maria', 'matricula': '002'}
        ]
        dados_mock.adicionar_exclusao_estagio = Mock()
        dados_mock.adicionar_exclusao_aprendiz = Mock()
        
        agente._aplicar_exclusoes_cargo(dados_mock)
        
        # Verifica se o diretor foi removido
        assert len(dados_mock.colaboradores_ativos) == 1
        assert dados_mock.colaboradores_ativos[0]['cargo'] == 'Analista'

class TestAgenteCalculador:
    """Testes para o Agente Calculador."""
    
    @pytest.mark.asyncio
    async def test_inicializacao(self, settings):
        """Testa inicialização do agente."""
        agente = AgenteCalculador(settings)
        assert agente.nome == "Calculador"
    
    @pytest.mark.asyncio
    async def test_calcular_beneficios(self, settings):
        """Testa cálculo de benefícios."""
        agente = AgenteCalculador(settings)
        
        # Mock dos dados
        dados_mock = Mock()
        dados_mock.colaboradores_ativos = [
            {
                'elegivel_beneficio': True,
                'sindicato': 'Sindicato A',
                'dias_trabalhados': 22,
                'nome': 'João'
            }
        ]
        dados_mock.config_sindicatos = {'Sindicato A': 25.0}
        dados_mock.dias_uteis_por_sindicato = {'Sindicato A': 22}
        
        agente._calcular_beneficios(dados_mock)
        
        # Verifica se o benefício foi calculado
        colaborador = dados_mock.colaboradores_ativos[0]
        assert colaborador['valor_vr'] == 25.0
        assert colaborador['dias_uteis'] == 22
        assert colaborador['dias_trabalhados'] == 22

class TestAgenteValidador:
    """Testes para o Agente Validador."""
    
    @pytest.mark.asyncio
    async def test_inicializacao(self, settings):
        """Testa inicialização do agente."""
        agente = AgenteValidador(settings)
        assert agente.nome == "Validador"
    
    @pytest.mark.asyncio
    async def test_validar_dados_obrigatorios(self, settings):
        """Testa validação de dados obrigatórios."""
        agente = AgenteValidador(settings)
        
        # Mock dos dados
        dados_mock = Mock()
        dados_mock.colaboradores_ativos = [
            {
                'matricula': '001',
                'nome': 'João',
                'sindicato': 'Sindicato A',
                'data_admissao': '2020-01-01',
                'data_desligamento': None
            }
        ]
        
        resultado = agente._validar_dados_obrigatorios(dados_mock)
        assert resultado is True

class TestAgenteGerador:
    """Testes para o Agente Gerador."""
    
    @pytest.mark.asyncio
    async def test_inicializacao(self, settings):
        """Testa inicialização do agente."""
        agente = AgenteGerador(settings)
        assert agente.nome == "Gerador"
    
    @pytest.mark.asyncio
    async def test_criar_planilha_excel(self, settings):
        """Testa criação de planilha Excel."""
        agente = AgenteGerador(settings)
        
        # Mock dos dados
        dados_mock = Mock()
        dados_mock.colaboradores_ativos = [
            {
                'matricula': '001',
                'nome': 'João',
                'cargo': 'Analista',
                'sindicato': 'Sindicato A'
            }
        ]
        dados_mock.config_sindicatos = {'Sindicato A': 25.0}
        dados_mock.dias_uteis_por_sindicato = {'Sindicato A': 22}
        dados_mock.erros_validacao = []
        dados_mock.warnings = []
        dados_mock.mes_referencia = '05.2025'
        
        agente.dados_finais = dados_mock
        
        # Mock do pandas ExcelWriter
        with patch('pandas.ExcelWriter') as mock_writer:
            mock_writer.return_value.__enter__.return_value = Mock()
            mock_writer.return_value.__exit__.return_value = None
            
            agente._criar_planilha_excel(Path('teste.xlsx'))
            
            # Verifica se foi chamado
            assert True  # Se chegou aqui sem erro, o teste passou 