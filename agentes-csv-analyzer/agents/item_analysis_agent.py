import pandas as pd
import numpy as np
from typing import Dict, List, Union

class ItemAnalysisAgent:
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

    def analyze_numeric_distributions(self) -> Dict:
        """Analisa a distribuição de todas as colunas numéricas."""
        results = {}
        for num_col in self.numeric_columns:
            try:
                series = self.df[num_col]
                results[num_col] = {
                    'total': float(series.sum()),
                    'mean': float(series.mean()),
                    'median': float(series.median()),
                    'std': float(series.std()),
                    'min': float(series.min()),
                    'max': float(series.max()),
                    'unique_values': int(series.nunique())
                }
            except:
                continue
        return results

    def analyze_text_frequencies(self) -> Dict:
        """Analisa frequências de valores em colunas de texto."""
        results = {}
        for text_col in self.text_columns:
            try:
                value_counts = self.df[text_col].value_counts()
                if len(value_counts) > 0:
                    top_value = value_counts.index[0]
                    results[text_col] = {
                        'most_common': top_value,
                        'most_common_count': int(value_counts[top_value]),
                        'unique_values': int(len(value_counts)),
                        'top_5': value_counts.head().to_dict()
                    }
            except:
                continue
        return results

    def analyze_temporal_patterns(self) -> Dict:
        """Analisa padrões temporais para todas as métricas numéricas."""
        results = {}
        for date_col in self.date_columns:
            try:
                self.df['_temp_date'] = pd.to_datetime(self.df[date_col]).dt.date
                analysis = {}
                
                for num_col in self.numeric_columns:
                    daily_stats = self.df.groupby('_temp_date')[num_col].agg(['sum', 'mean', 'count'])
                    max_date = daily_stats['sum'].idxmax()
                    
                    analysis[num_col] = {
                        'peak_date': max_date.strftime('%Y-%m-%d'),
                        'peak_total': float(daily_stats.loc[max_date, 'sum']),
                        'peak_average': float(daily_stats.loc[max_date, 'mean']),
                        'peak_count': int(daily_stats.loc[max_date, 'count']),
                        'overall_daily_average': float(daily_stats['mean'].mean())
                    }
                
                if analysis:
                    results[date_col] = analysis
                self.df.drop('_temp_date', axis=1, inplace=True)
            except:
                continue
        return results

    def analyze_correlations(self) -> Dict:
        """Analisa correlações entre colunas numéricas."""
        if len(self.numeric_columns) < 2:
            return {}
            
        try:
            corr_matrix = self.df[self.numeric_columns].corr()
            correlations = {}
            
            for col1 in self.numeric_columns:
                strong_correlations = []
                for col2 in self.numeric_columns:
                    if col1 != col2:
                        corr_value = corr_matrix.loc[col1, col2]
                        if abs(corr_value) > 0.5:  # Correlações significativas
                            strong_correlations.append({
                                'with': col2,
                                'correlation': float(corr_value)
                            })
                if strong_correlations:
                    correlations[col1] = strong_correlations
            
            return correlations
        except:
            return {}

    def get_summary(self) -> Dict:
        """Retorna um resumo completo das análises."""
        try:
            return {
                'numeric_distributions': self.analyze_numeric_distributions(),
                'text_patterns': self.analyze_text_frequencies(),
                'temporal_patterns': self.analyze_temporal_patterns(),
                'correlations': self.analyze_correlations(),
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