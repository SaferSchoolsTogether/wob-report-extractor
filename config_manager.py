import pandas as pd
import os

class ConfigManager:
    def __init__(self):
        self.config_file = "extraction_config.xlsx"
        self.load_or_create_config()
    
    def load_or_create_config(self):
        if not os.path.exists(self.config_file):
            self.create_default_config()
        
        # Load configurations
        self.patterns_df = pd.read_excel(self.config_file, sheet_name='Patterns')
        self.districts_df = pd.read_excel(self.config_file, sheet_name='Districts')
    
    def create_default_config(self):
        with pd.ExcelWriter(self.config_file) as writer:
            # Patterns sheet
            patterns = pd.DataFrame({
                'Pattern_Name': ['SOC_Header', 'Social_Media', 'Checkbox_Checked', 'Checkbox_Unchecked'],
                'Pattern_Text': ['Subject of Concern', 'Information & Activity', '☒', '☐'],
                'Alternative_1': ['SOC:', 'Username:', '[X]', '[ ]'],
                'Alternative_2': ['Subject:', 'Display Name:', '✓', '']
            })
            patterns.to_excel(writer, sheet_name='Patterns', index=False)
            
            # Districts sheet  
            districts = pd.DataFrame({
                'District_Name': ['SD73', 'Dodge County', 'Default'],
                'Report_Format': ['checkbox', 'table', 'checkbox'],
                'Special_Rules': ['none', 'concerns_in_table', 'none']
            })
            districts.to_excel(writer, sheet_name='Districts', index=False)