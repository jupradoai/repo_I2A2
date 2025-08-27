"""
Agente Consolidador - Consolida dados de múltiplas bases.
"""

import asyncio
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from .base import BaseAgente
from models.dados_entrada import DadosEntrada
from config.settings import Settings

class AgenteConsolidador(BaseAgente):
    """Consolida todas as bases de dados em uma única estrutura."""
    
    def __init__(self, settings: Settings):
        super().__init__(settings, "Consolidador")
        
    async def _executar_agente(self, dados_entrada: Any = None) -> DadosEntrada:
        """Executa a consolidação de todas as bases."""
        try:
            self.logger.info("📊 Iniciando consolidação das bases...")
            
            dados = DadosEntrada()
            
            # Define a competência dinamicamente
            self._definir_competencia(dados)
            
            # Lê todas as bases
            await self._ler_todas_bases(dados)
            
            self.logger.info(f"✅ Consolidação concluída: {dados.total_registros} registros")
            return dados
            
        except Exception as e:
            self.logger.error(f"❌ Erro na consolidação: {e}")
            raise
    
    def _definir_competencia(self, dados: DadosEntrada):
        """Define a competência do mês dinamicamente."""
        try:
            # Obtém mês e ano atual
            hoje = datetime.now()
            mes_atual = hoje.month
            ano_atual = hoje.year
            
            # Formata competência (MM.YYYY)
            competencia = f"{mes_atual:02d}.{ano_atual}"
            
            # Define no modelo
            dados.definir_competencia(competencia)
            
            # Adiciona observação
            dados.adicionar_observacao_geral(f"Competência processada: {competencia}")
            
            self.logger.info(f"✅ Competência definida: {competencia}")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao definir competência: {e}")
            # Define competência padrão em caso de erro
            dados.definir_competencia("05.2025")
    
    async def _ler_todas_bases(self, dados: DadosEntrada):
        """Lê todas as bases de dados de forma otimizada."""
        
        # Mapeamento de arquivos e suas funções de leitura
        bases = {
            'ativos': self._ler_ativos,
            'ferias': self._ler_ferias,
            'desligados': self._ler_desligados,
            'admissao': self._ler_admissao,
            'sindicato_valor': self._ler_sindicato_valor,
            'dias_uteis': self._ler_dias_uteis,
            'exterior': self._ler_exterior,
            'estagio': self._ler_estagio,
            'aprendiz': self._ler_aprendiz,
            'afastamentos': self._ler_afastamentos
        }
        
        for nome_base, funcao_ler in bases.items():
            try:
                await funcao_ler(dados)
            except FileNotFoundError:
                self.logger.warning(f"⚠️ Arquivo {nome_base} não encontrado")
            except Exception as e:
                self.adicionar_erro(f"Erro ao ler {nome_base}: {e}")
        
        # Após carregar todas as bases, preencher dias_uteis faltantes com a planilha real
        try:
            preenchidos = 0
            for c in dados.colaboradores_ativos:
                if not c.get('dias_uteis') or int(c.get('dias_uteis') or 0) <= 0:
                    du = dados.dias_uteis_por_sindicato.get(c.get('sindicato'))
                    if du:
                        c['dias_uteis'] = du
                        preenchidos += 1
            if preenchidos:
                self.logger.info(f"✅ Dias úteis preenchidos a partir da planilha: {preenchidos}")
        except Exception as e:
            self.logger.warning(f"Falha ao preencher dias úteis: {e}")
    
    def _normalizar_sindicato(self, texto: str) -> str:
        """Normaliza o nome do sindicato para chaves de estado usadas nas planilhas (Paraná, Rio de Janeiro, Rio Grande do Sul, São Paulo)."""
        if not texto:
            return ''
        t = str(texto).upper()
        if 'RIO GRANDE DO SUL' in t or ' RS' in t or t.startswith('RS '):
            return 'Rio Grande do Sul'
        if 'RIO DE JANEIRO' in t or ' RJ' in t or t.startswith('RJ '):
            return 'Rio de Janeiro'
        if 'CURITIBA' in t or ' PARANA' in t or 'PARANÁ' in t or ' PR' in t or t.startswith('PR '):
            return 'Paraná'
        if 'SAO PAULO' in t or 'SÃO PAULO' in t or ' ESTADO DE SP' in t or ' SP' in t or t.startswith('SP '):
            return 'São Paulo'
        # fallback: mantém texto capitalizado básico
        return texto.strip()
    
    async def _ler_ativos(self, dados: DadosEntrada):
        """Lê base de colaboradores ativos."""
        arquivo = self.settings.DATA_DIR / self.settings.ARQUIVOS_ENTRADA["ativos"]
        df = pd.read_excel(arquivo)
        
        # Detecta colunas possíveis
        nome_aliases = [
            'NOME', 'Nome', 'NOME COLABORADOR', 'NOME DO COLABORADOR', 'NOME COMPLETO',
            'COLABORADOR', 'FUNCIONARIO', 'FUNCIONÁRIO'
        ]
        sindicato_aliases = ['Sindicato', 'SINDICATO']
        cpf_aliases = ['CPF', 'CPF COLABORADOR']
        cargo_aliases = ['TITULO DO CARGO', 'CARGO', 'TÍTULO DO CARGO']
        situacao_aliases = ['DESC. SITUACAO', 'SITUAÇÃO', 'DESC SITUACAO']
        empresa_aliases = ['EMPRESA', 'Empresa']
        adm_aliases = ['DATA ADMISSÃO', 'DATA ADM', 'Admissão', 'DATA DE ADMISSÃO']
        dias_uteis_aliases = ['DIAS UTEIS', 'DIAS ÚTEIS', 'DIAS UTEIS MÊS', 'DIAS UTEIS MES', 'DIAS_UTEIS']
        dias_trab_aliases = ['DIAS TRABALHADOS', 'DIAS TRAB.', 'DIAS TRAB', 'DIAS_TRABALHADOS']
        
        def pick(colnames: List[str]) -> str:
            for c in colnames:
                if c in df.columns:
                    return c
            return None
        
        col_nome = pick(nome_aliases)
        col_sindicato = pick(sindicato_aliases)
        col_cpf = pick(cpf_aliases)
        col_cargo = pick(cargo_aliases)
        col_situacao = pick(situacao_aliases)
        col_empresa = pick(empresa_aliases)
        col_adm = pick(adm_aliases)
        col_dias_uteis = pick(dias_uteis_aliases)
        col_dias_trab = pick(dias_trab_aliases)
        
        for _, row in df.iterrows():
            sindicato_raw = (str(row.get(col_sindicato)).strip() if col_sindicato else '')
            sindicato_norm = self._normalizar_sindicato(sindicato_raw)
            colaborador = {
                'matricula': row.get('MATRICULA') if 'MATRICULA' in df.columns else row.get('Matricula'),
                'nome': (str(row.get(col_nome)).strip() if col_nome else ''),
                'cpf': (str(row.get(col_cpf)).strip() if col_cpf else ''),
                'empresa': (str(row.get(col_empresa)).strip() if col_empresa else ''),
                'cargo': (str(row.get(col_cargo)).strip() if col_cargo else ''),
                'situacao': (str(row.get(col_situacao)).strip() if col_situacao else ''),
                'sindicato_raw': sindicato_raw,
                'sindicato': sindicato_norm,
                'data_admissao': row.get(col_adm) if col_adm else None,
                'dias_uteis': int(row.get(col_dias_uteis)) if col_dias_uteis and pd.notna(row.get(col_dias_uteis)) else None,
                'dias_trabalhados': int(row.get(col_dias_trab)) if col_dias_trab and pd.notna(row.get(col_dias_trab)) else None,
            }
            dados.adicionar_colaborador_ativo(colaborador)
        
        self.logger.info(f"✅ ATIVOS: {len(df)} registros")
    
    async def _ler_ferias(self, dados: DadosEntrada):
        """Lê base de colaboradores em férias."""
        arquivo = self.settings.DATA_DIR / self.settings.ARQUIVOS_ENTRADA["ferias"]
        df = pd.read_excel(arquivo)
        
        for _, row in df.iterrows():
            colaborador = {
                'matricula': row['MATRICULA'],
                'situacao': row['DESC. SITUACAO'],
                'dias_ferias': row['DIAS DE FÉRIAS'],
                'em_ferias': True  # Marca como em férias
            }
            dados.adicionar_colaborador_ferias(colaborador)
        
        self.logger.info(f"✅ FÉRIAS: {len(df)} registros")
    
    async def _ler_desligados(self, dados: DadosEntrada):
        """Lê base de colaboradores desligados."""
        arquivo = self.settings.DATA_DIR / self.settings.ARQUIVOS_ENTRADA["desligados"]
        df = pd.read_excel(arquivo)
        
        for _, row in df.iterrows():
            colaborador = {
                'matricula': row['MATRICULA '],  # Note o espaço extra
                'data_demissao': row['DATA DEMISSÃO'],
                'comunicado': row['COMUNICADO DE DESLIGAMENTO']
            }
            dados.adicionar_colaborador_desligado(colaborador)
        
        self.logger.info(f"✅ DESLIGADOS: {len(df)} registros")
    
    async def _ler_admissao(self, dados: DadosEntrada):
        """Lê base de colaboradores admitidos."""
        arquivo = self.settings.DATA_DIR / self.settings.ARQUIVOS_ENTRADA["admissao"]
        df = pd.read_excel(arquivo)
        
        for _, row in df.iterrows():
            colaborador = {
                'matricula': row['MATRICULA'],
                'admissao': row['Admissão'],
                'cargo': row['Cargo'],
                'data_admissao': row['Admissão']  # Adiciona campo de data
            }
            dados.adicionar_colaborador_admissao(colaborador)
        
        self.logger.info(f"✅ ADMISSÃO: {len(df)} registros")
    
    async def _ler_sindicato_valor(self, dados: DadosEntrada):
        """Lê configuração de valores por estado (Paraná, RJ, RS, SP)."""
        arquivo = self.settings.DATA_DIR / self.settings.ARQUIVOS_ENTRADA["sindicato_valor"]
        df = pd.read_excel(arquivo)
        
        # Primeira coluna é o estado, segunda é o valor
        for _, row in df.iterrows():
            chave = str(row.iloc[0]).strip()
            valor = row.iloc[1]
            if pd.notna(chave) and pd.notna(valor):
                dados.configurar_sindicato(chave, float(valor))
        
        self.logger.info(f"✅ SINDICATO x VALOR: {len(df)} configurações")
    
    async def _ler_dias_uteis(self, dados: DadosEntrada):
        """Lê dias úteis por estado normalizado a partir das legendas de sindicato."""
        arquivo = self.settings.DATA_DIR / self.settings.ARQUIVOS_ENTRADA["dias_uteis"]
        df = pd.read_excel(arquivo)
        
        # Pula a primeira linha de cabeçalho com rótulos
        for _, row in df.iloc[1:].iterrows():
            raw = row.iloc[0]
            dias = row.iloc[1]
            if pd.notna(raw) and pd.notna(dias):
                chave = self._normalizar_sindicato(str(raw))
                try:
                    dados.configurar_dias_uteis(chave, int(dias))
                except Exception:
                    # Tenta converter strings com espaços/etiquetas
                    try:
                        dados.configurar_dias_uteis(chave, int(str(dias).strip()))
                    except Exception:
                        continue
        
        self.logger.info(f"✅ DIAS ÚTEIS: {len(df)-1} configurações")
    
    async def _ler_exterior(self, dados: DadosEntrada):
        """Lê base de colaboradores no exterior."""
        arquivo = self.settings.DATA_DIR / self.settings.ARQUIVOS_ENTRADA["exterior"]
        df = pd.read_excel(arquivo)
        
        for _, row in df.iterrows():
            matricula = row['Cadastro']
            if pd.notna(matricula):
                dados.adicionar_exclusao_exterior(str(matricula))
        
        self.logger.info(f"✅ EXTERIOR: {len(df)} exclusões")
    
    async def _ler_estagio(self, dados: DadosEntrada):
        """Lê base de estagiários."""
        arquivo = self.settings.DATA_DIR / self.settings.ARQUIVOS_ENTRADA["estagio"]
        df = pd.read_excel(arquivo)
        
        for _, row in df.iterrows():
            matricula = row['MATRICULA']
            if pd.notna(matricula):
                dados.adicionar_exclusao_estagio(str(matricula))
        
        self.logger.info(f"✅ ESTÁGIO: {len(df)} exclusões")
    
    async def _ler_aprendiz(self, dados: DadosEntrada):
        """Lê base de aprendizes."""
        arquivo = self.settings.DATA_DIR / self.settings.ARQUIVOS_ENTRADA["aprendiz"]
        df = pd.read_excel(arquivo)
        
        for _, row in df.iterrows():
            matricula = row['MATRICULA']
            if pd.notna(matricula):
                dados.adicionar_exclusao_aprendiz(str(matricula))
        
        self.logger.info(f"✅ APRENDIZ: {len(df)} exclusões")
    
    async def _ler_afastamentos(self, dados: DadosEntrada):
        """Lê base de colaboradores afastados."""
        arquivo = self.settings.DATA_DIR / self.settings.ARQUIVOS_ENTRADA["afastamentos"]
        df = pd.read_excel(arquivo)
        
        for _, row in df.iterrows():
            matricula = row['MATRICULA']
            if pd.notna(matricula):
                dados.adicionar_exclusao_afastado(str(matricula))
        
        self.logger.info(f"✅ AFASTAMENTOS: {len(df)} exclusões") 