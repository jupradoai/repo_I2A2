import pandas as pd
import numpy as np
from typing import Dict, List, Union

class SupplierAnalysisAgent:
    def __init__(self, df: pd.DataFrame = None):
        self.df = df
        self.numeric_columns = []
        self.text_columns = []
        self.date_columns = []

    def set_dataframe(self, df: pd.DataFrame) -> None:
        """Define o DataFrame para análise e categoriza as colunas."""
        self.df = df
        self._categorize_columns()
        print("\nAnálise das colunas encontradas:")
        print(f"Colunas numéricas: {self.numeric_columns}")
        print(f"Colunas de texto: {self.text_columns}")
        print(f"Colunas de data: {self.date_columns}")

    def _categorize_columns(self) -> None:
        """Categoriza automaticamente as colunas do DataFrame."""
        for col in self.df.columns:
            # Tenta converter para datetime
            try:
                pd.to_datetime(self.df[col])
                self.date_columns.append(col)
                continue
            except:
                pass
            
            # Verifica se é numérica
            if pd.api.types.is_numeric_dtype(self.df[col]):
                self.numeric_columns.append(col)
            else:
                self.text_columns.append(col)

    def get_total_by_entity(self, entity_col: str, value_col: str) -> pd.Series:
        """Análise genérica de totais por entidade."""
        return self.df.groupby(entity_col)[value_col].sum().sort_values(ascending=False)

    def analyze_all_numeric_by_text(self) -> Dict:
        """Analisa todas as combinações de colunas numéricas agrupadas por texto."""
        results = {}
        for text_col in self.text_columns:
            analysis = {}
            for num_col in self.numeric_columns:
                try:
                    totals = self.get_total_by_entity(text_col, num_col)
                    if len(totals) > 0:
                        top_entity = totals.index[0]
                        analysis[num_col] = {
                            'top_entity': top_entity,
                            'top_value': float(totals[top_entity]),
                            'total': float(totals.sum()),
                            'mean': float(totals.mean()),
                            'count': len(totals)
                        }
                except:
                    continue
            if analysis:
                results[text_col] = analysis
        return results

    def get_time_series_analysis(self) -> Dict:
        """Analisa tendências temporais para todas as colunas numéricas."""
        results = {}
        for date_col in self.date_columns:
            try:
                self.df['_temp_date'] = pd.to_datetime(self.df[date_col]).dt.date
                analysis = {}
                for num_col in self.numeric_columns:
                    daily_values = self.df.groupby('_temp_date')[num_col].sum()
                    if len(daily_values) > 0:
                        max_date = daily_values.idxmax()
                        analysis[num_col] = {
                            'max_date': max_date.strftime('%Y-%m-%d'),
                            'max_value': float(daily_values[max_date]),
                            'total': float(daily_values.sum()),
                            'daily_average': float(daily_values.mean())
                        }
                if analysis:
                    results[date_col] = analysis
                self.df.drop('_temp_date', axis=1, inplace=True)
            except:
                continue
        return results

    def get_summary(self) -> Dict:
        """Retorna um resumo completo das análises."""
        try:
            # Análise de todas as combinações de texto/número
            entity_analysis = self.analyze_all_numeric_by_text()
            
            # Análise temporal
            time_analysis = self.get_time_series_analysis()
            
            # Estatísticas gerais
            general_stats = {}
            for num_col in self.numeric_columns:
                try:
                    general_stats[num_col] = {
                        'total': float(self.df[num_col].sum()),
                        'mean': float(self.df[num_col].mean()),
                        'max': float(self.df[num_col].max()),
                        'min': float(self.df[num_col].min())
                    }
                except:
                    continue
            
            return {
                'entity_analysis': entity_analysis,
                'time_analysis': time_analysis,
                'general_stats': general_stats,
                'column_types': {
                    'numeric': self.numeric_columns,
                    'text': self.text_columns,
                    'dates': self.date_columns
                }
            }
        except Exception as e:
            return {
                "error": str(e),
                "colunas_disponiveis": list(self.df.columns)
            }

    def get_total_by_supplier(self) -> pd.Series:
        """Calcula o montante total recebido por fornecedor."""
        if 'fornecedor' not in self.columns_map or 'valor' not in self.columns_map:
            raise ValueError("Colunas necessárias não encontradas no DataFrame")
            
        return self.df.groupby(self.columns_map['fornecedor'])[self.columns_map['valor']].sum().sort_values(ascending=False)

    def get_invoices_by_supplier(self) -> pd.Series:
        """Conta o número de notas fiscais por fornecedor."""
        if 'fornecedor' not in self.columns_map:
            raise ValueError("Coluna de fornecedor não encontrada no DataFrame")
            
        return self.df.groupby(self.columns_map['fornecedor']).size().sort_values(ascending=False)

    def get_supplier_summary(self) -> Dict:
        """Retorna um resumo das informações por fornecedor."""
        if not self.columns_map:
            return {
                "error": "Não foi possível identificar as colunas necessárias no DataFrame",
                "colunas_disponiveis": list(self.df.columns)
            }
            
        try:
            total_by_supplier = self.get_total_by_supplier()
            invoices_by_supplier = self.get_invoices_by_supplier()
            
            top_supplier = total_by_supplier.index[0]
            return {
                'top_supplier': {
                    'name': top_supplier,
                    'total_value': float(total_by_supplier[top_supplier]),
                    'total_invoices': int(invoices_by_supplier[top_supplier])
                },
                'all_suppliers': {
                    'total_value': float(self.df[self.columns_map['valor']].sum()) if 'valor' in self.columns_map else 0,
                    'total_invoices': len(self.df)
                },
                'columns_used': self.columns_map
            }
        except Exception as e:
            return {
                "error": str(e),
                "colunas_disponiveis": list(self.df.columns),
                "mapeamento_tentado": self.columns_map
            }

    def get_supplier_monthly_analysis(self) -> pd.DataFrame:
        """Analisa o montante mensal por fornecedor."""
        if 'fornecedor' not in self.columns_map or 'valor' not in self.columns_map:
            raise ValueError("Colunas necessárias não encontradas no DataFrame")
            
        # Procura uma coluna de data
        date_options = ['data', 'data_emissao', 'data emissao', 'emissao', 'data_nota', 'data nota']
        date_col = None
        columns = [col.lower() for col in self.df.columns]
        
        for opt in date_options:
            if opt in columns:
                date_col = self.df.columns[columns.index(opt)]
                break
        
        if not date_col:
            raise ValueError("Coluna de data não encontrada")
            
        self.df['mes'] = pd.to_datetime(self.df[date_col]).dt.to_period('M')
        monthly_analysis = self.df.pivot_table(
            index=self.columns_map['fornecedor'],
            columns='mes',
            values=self.columns_map['valor'],
            aggfunc='sum',
            fill_value=0
        )
        return monthly_analysis

    def get_top_suppliers(self, n: int = 5) -> List[Dict]:
        """Retorna os N fornecedores com maior montante."""
        try:
            top_suppliers = self.get_total_by_supplier().head(n)
            return [
                {
                    'name': supplier,
                    'total_value': float(value)
                }
                for supplier, value in top_suppliers.items()
            ]
        except Exception as e:
            return [{"error": str(e)}] 