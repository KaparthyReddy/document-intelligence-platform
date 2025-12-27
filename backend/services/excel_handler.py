import pandas as pd
import openpyxl
from pathlib import Path
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class ExcelHandler:
    """Handle Excel/spreadsheet document processing"""
    
    def __init__(self):
        self.supported_formats = ['.xlsx', '.xls', '.csv']
    
    async def extract_data(self, file_path: str) -> Dict:
        """
        Extract data from Excel file
        
        Returns:
            {
                'sheets': List[Dict],
                'summary': Dict,
                'text': str
            }
        """
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.csv':
                return await self._process_csv(file_path)
            else:
                return await self._process_excel(file_path)
                
        except Exception as e:
            logger.error(f"Excel extraction error: {e}")
            return {
                'sheets': [],
                'summary': {},
                'text': '',
                'error': str(e)
            }
    
    async def _process_excel(self, file_path: str) -> Dict:
        """Process Excel file (.xlsx, .xls)"""
        # Read all sheets
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        
        sheets_data = []
        all_text = []
        
        for sheet_name in sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Convert to text
            sheet_text = df.to_string(index=False)
            all_text.append(f"Sheet: {sheet_name}\n{sheet_text}")
            
            # Get sheet info
            sheet_info = {
                'name': sheet_name,
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': df.columns.tolist(),
                'preview': df.head(5).to_dict('records'),
                'has_numeric': any(df[col].dtype in ['int64', 'float64'] for col in df.columns),
                'has_dates': any(df[col].dtype == 'datetime64[ns]' for col in df.columns)
            }
            
            sheets_data.append(sheet_info)
        
        # Get summary statistics
        summary = {
            'total_sheets': len(sheet_names),
            'sheet_names': sheet_names,
            'file_format': Path(file_path).suffix
        }
        
        return {
            'sheets': sheets_data,
            'summary': summary,
            'text': '\n\n'.join(all_text)
        }
    
    async def _process_csv(self, file_path: str) -> Dict:
        """Process CSV file"""
        df = pd.read_csv(file_path)
        
        # Convert to text
        text = df.to_string(index=False)
        
        sheet_info = {
            'name': 'CSV Data',
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': df.columns.tolist(),
            'preview': df.head(10).to_dict('records'),
            'has_numeric': any(df[col].dtype in ['int64', 'float64'] for col in df.columns),
            'has_dates': any(df[col].dtype == 'datetime64[ns]' for col in df.columns)
        }
        
        return {
            'sheets': [sheet_info],
            'summary': {
                'total_sheets': 1,
                'sheet_names': ['CSV Data'],
                'file_format': '.csv'
            },
            'text': text
        }
    
    async def detect_data_types(self, file_path: str) -> Dict:
        """
        Detect data types and patterns in spreadsheet
        """
        try:
            df = pd.read_excel(file_path) if Path(file_path).suffix != '.csv' else pd.read_csv(file_path)
            
            type_info = {}
            for col in df.columns:
                type_info[col] = {
                    'dtype': str(df[col].dtype),
                    'non_null_count': int(df[col].count()),
                    'null_count': int(df[col].isnull().sum()),
                    'unique_values': int(df[col].nunique())
                }
                
                # Add statistics for numeric columns
                if df[col].dtype in ['int64', 'float64']:
                    type_info[col]['statistics'] = {
                        'mean': float(df[col].mean()),
                        'median': float(df[col].median()),
                        'min': float(df[col].min()),
                        'max': float(df[col].max()),
                        'std': float(df[col].std())
                    }
            
            return type_info
            
        except Exception as e:
            logger.error(f"Data type detection error: {e}")
            return {}
    
    async def extract_financial_data(self, file_path: str) -> Dict:
        """
        Extract financial data (amounts, dates, categories)
        """
        try:
            df = pd.read_excel(file_path) if Path(file_path).suffix != '.csv' else pd.read_csv(file_path)
            
            financial_data = {
                'amounts': [],
                'dates': [],
                'categories': []
            }
            
            # Find numeric columns (potential amounts)
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            for col in numeric_cols:
                if any(keyword in col.lower() for keyword in ['amount', 'total', 'price', 'cost', 'balance']):
                    financial_data['amounts'].append({
                        'column': col,
                        'total': float(df[col].sum()),
                        'average': float(df[col].mean()),
                        'values': df[col].tolist()
                    })
            
            # Find date columns
            date_cols = df.select_dtypes(include=['datetime64']).columns
            for col in date_cols:
                financial_data['dates'].append({
                    'column': col,
                    'min_date': str(df[col].min()),
                    'max_date': str(df[col].max())
                })
            
            # Find categorical columns
            categorical_cols = df.select_dtypes(include=['object']).columns
            for col in categorical_cols:
                if df[col].nunique() < 20:  # Reasonable number of categories
                    financial_data['categories'].append({
                        'column': col,
                        'unique_values': df[col].unique().tolist()
                    })
            
            return financial_data
            
        except Exception as e:
            logger.error(f"Financial data extraction error: {e}")
            return {
                'amounts': [],
                'dates': [],
                'categories': []
            }
    
    async def create_summary_report(self, file_path: str) -> str:
        """
        Create a text summary report of the spreadsheet
        """
        try:
            df = pd.read_excel(file_path) if Path(file_path).suffix != '.csv' else pd.read_csv(file_path)
            
            summary_lines = [
                f"Spreadsheet Summary Report",
                f"=" * 50,
                f"Total Rows: {len(df)}",
                f"Total Columns: {len(df.columns)}",
                f"Columns: {', '.join(df.columns.tolist())}",
                "",
                "Column Statistics:",
                "-" * 50
            ]
            
            for col in df.columns:
                summary_lines.append(f"\n{col}:")
                summary_lines.append(f"  Type: {df[col].dtype}")
                summary_lines.append(f"  Non-null: {df[col].count()}")
                summary_lines.append(f"  Unique values: {df[col].nunique()}")
                
                if df[col].dtype in ['int64', 'float64']:
                    summary_lines.append(f"  Mean: {df[col].mean():.2f}")
                    summary_lines.append(f"  Min: {df[col].min():.2f}")
                    summary_lines.append(f"  Max: {df[col].max():.2f}")
            
            return '\n'.join(summary_lines)
            
        except Exception as e:
            logger.error(f"Summary report creation error: {e}")
            return f"Error creating summary: {str(e)}"