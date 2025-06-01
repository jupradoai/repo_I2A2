import os
import zipfile
import pandas as pd
from typing import List, Dict, Union

class LoaderAgent:
    def __init__(self, data_dir: str = "../data"):
        self.data_dir = data_dir
        self.dataframes: Dict[str, pd.DataFrame] = {}

    def extract_zip(self, zip_path: str) -> List[str]:
        """Extrai arquivos de um ZIP para o diretório de dados."""
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.data_dir)
            return [f for f in zip_ref.namelist() if f.endswith('.csv')]

    def load_csv(self, csv_path: str, filename: str) -> None:
        """Carrega um arquivo CSV como DataFrame."""
        try:
            # Primeiro, vamos ler o CSV para ver suas colunas
            df = pd.read_csv(os.path.join(self.data_dir, csv_path), nrows=1)
            print(f"\nColunas encontradas em {filename}:")
            print(df.columns.tolist())
            
            # Configuramos o parse_dates apenas se a coluna existir
            parse_dates = ['data_emissao'] if 'data_emissao' in df.columns else None
            
            # Agora lemos o arquivo completo
            df = pd.read_csv(
                os.path.join(self.data_dir, csv_path),
                parse_dates=parse_dates,
                decimal='.'
            )
            
            self.dataframes[filename] = df
            print(f"✅ Arquivo {filename} carregado com sucesso!")
            print(f"   Dimensões: {df.shape[0]} linhas x {df.shape[1]} colunas")
            
        except Exception as e:
            print(f"❌ Erro ao carregar {filename}: {str(e)}")

    def process_zip_file(self, zip_path: str) -> bool:
        """Processa um arquivo ZIP contendo CSVs."""
        try:
            csv_files = self.extract_zip(zip_path)
            print(f"\nArquivos encontrados no ZIP:")
            for csv_file in csv_files:
                print(f"📄 {csv_file}")
            
            for csv_file in csv_files:
                self.load_csv(csv_file, os.path.basename(csv_file))
            
            if not self.dataframes:
                print("\n⚠️ Nenhum DataFrame foi carregado com sucesso!")
                return False
                
            return True
            
        except Exception as e:
            print(f"\n❌ Erro ao processar arquivo ZIP: {str(e)}")
            return False

    def get_dataframe(self, name: str) -> Union[pd.DataFrame, None]:
        """Retorna um DataFrame específico pelo nome."""
        return self.dataframes.get(name)

    def get_all_dataframes(self) -> Dict[str, pd.DataFrame]:
        """Retorna todos os DataFrames carregados."""
        return self.dataframes 