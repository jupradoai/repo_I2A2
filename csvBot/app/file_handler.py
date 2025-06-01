import os
import zipfile
import pandas as pd
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class FileHandler:
    def __init__(self):
        self.dataframes: Dict[str, pd.DataFrame] = {}
        self.temp_dir = "temp_csv_files"

    def process_zip_file(self, zip_file) -> Tuple[bool, str]:
        """
        Processa o arquivo ZIP e extrai os CSVs
        """
        try:
            if not os.path.exists(self.temp_dir):
                os.makedirs(self.temp_dir)

            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                # Lista todos os arquivos no ZIP
                csv_files = [f for f in zip_ref.namelist() if f.lower().endswith('.csv')]
                
                if not csv_files:
                    return False, "Nenhum arquivo CSV encontrado no ZIP."

                # Extrai apenas os arquivos CSV
                zip_ref.extractall(self.temp_dir, members=csv_files)

                # Processa cada arquivo CSV
                for csv_file in csv_files:
                    success, message = self._process_csv_file(os.path.join(self.temp_dir, csv_file))
                    if not success:
                        return False, f"Erro ao processar {csv_file}: {message}"

            return True, f"Processados com sucesso {len(csv_files)} arquivos CSV."

        except Exception as e:
            return False, f"Erro ao processar arquivo ZIP: {str(e)}"

    def _process_csv_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Processa um arquivo CSV individual conforme especificações:
        - Campos separados por vírgulas
        - Decimais com ponto
        - Datas no formato AAAA-MM-DD HH:MN:SS
        """
        try:
            # Gera um nome adequado para o DataFrame
            df_name = "df_" + os.path.basename(file_path).replace('.csv', '').replace('-', '_')
            
            # Lê o CSV com as configurações específicas
            df = pd.read_csv(
                file_path,
                sep=',',
                decimal='.',
                dtype={
                    'VALOR NOTA FISCAL': float,
                    'VALOR TOTAL': float,
                    'UF EMITENTE': str,
                    'MODELO': str,
                    'RAZÃO SOCIAL EMITENTE': str,
                    'NOME DESTINATÁRIO': str,
                    'DESCRIÇÃO DO PRODUTO/SERVIÇO': str
                }
            )

            # Converte colunas de data usando o formato específico
            date_columns = [col for col in df.columns if 'DATA' in col.upper()]
            for col in date_columns:
                try:
                    df[col] = pd.to_datetime(df[col], format='%Y-%m-%d %H:%M:%S')
                except:
                    logger.warning(f"Não foi possível converter a coluna {col} para datetime")

            # Armazena o DataFrame no dicionário
            self.dataframes[df_name] = df
            return True, f"Arquivo {file_path} processado com sucesso."

        except Exception as e:
            return False, str(e)

    def get_available_dataframes(self) -> List[str]:
        """
        Retorna a lista de DataFrames disponíveis
        """
        return list(self.dataframes.keys())

    def get_dataframe(self, name: str) -> pd.DataFrame:
        """
        Retorna um DataFrame específico pelo nome
        """
        return self.dataframes.get(name)

    def cleanup(self):
        """
        Limpa os arquivos temporários
        """
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        self.dataframes.clear()
