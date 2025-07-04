import pandas as pd
import os
import re
from datetime import datetime

class OutputGenerator:
    def generate_reports(self, extracted_data, output_folder, month_year):
        timestamp = datetime.now().strftime("%Y%m%d")
        
        # 1. Account Tracker
        account_data = []
        for file_data in extracted_data:
            if 'error' not in file_data:
                for record in file_data.get('records', []):
                    # Base record info
                    base_info = {
                        'month': month_year,
                        'district': self.extract_district(file_data['file_name']),
                        'entity_nam': record.get('name', ''),
                        'school': record.get('school', ''),
                        'concerns': ', '.join([k for k, v in record.get('concerns', {}).items() if v])
                    }
                    
                    # Add social media records
                    for sm in record.get('social_media', []):
                        sm_record = base_info.copy()
                        sm_record.update({
                            'sm_typ': sm.get('platform', ''),
                            'us': sm.get('username', ''),
                            'url': sm.get('url', '')
                        })
                        account_data.append(sm_record)
                    
                    # If no social media, still add the record
                    if not record.get('social_media'):
                        account_data.append(base_info)
        
        if account_data:
            account_df = pd.DataFrame(account_data)
            account_file = os.path.join(output_folder, f"{timestamp} - Account Tracker ({month_year}).csv")
            account_df.to_csv(account_file, index=False)
        
        # 2. SOC List (BC districts only)
        soc_data = []
        for file_data in extracted_data:
            if 'error' not in file_data:
                district = self.extract_district(file_data['file_name'])
                if district.startswith('SD'):  # BC districts
                    for record in file_data.get('records', []):
                        soc_data.append({
                            'month': month_year,
                            'district': district,
                            'entity_nam': record.get('name', ''),
                            'school': record.get('school', ''),
                            'location': record.get('location', '')
                        })
        
        if soc_data:
            soc_df = pd.DataFrame(soc_data)
            soc_file = os.path.join(output_folder, f"{timestamp} - SOC List ({month_year}).csv")
            soc_df.to_csv(soc_file, index=False)
        
        # 3. Concerns Summary
        concerns_data = []
        for file_data in extracted_data:
            if 'error' not in file_data:
                for record in file_data.get('records', []):
                    row = {
                        'month': month_year,
                        'district': self.extract_district(file_data['file_name']),
                        'entity_nam': record.get('name', ''),
                        'school': record.get('school', '')
                    }
                    
                    # Add all concern categories as columns
                    all_concerns = record.get('concerns', {})
                    for concern_name, is_checked in all_concerns.items():
                        row[concern_name] = 1 if is_checked else 0
                    
                    concerns_data.append(row)
        
        if concerns_data:
            concerns_df = pd.DataFrame(concerns_data)
            concerns_file = os.path.join(output_folder, f"{timestamp} - WOB Concerns Data ({month_year}).csv")
            concerns_df.to_csv(concerns_file, index=False)
        
        return len(account_data), len(soc_data), len(concerns_data)
    
    def extract_district(self, filename):
        # Extract district from filename
        # Examples: "SD73 WOB Report - January 2025.pdf"
        #          "Dodge County WOB Report - January 2025.pdf"
        
        if 'SD' in filename and filename.index('SD') < 10:
            # Extract SD##
            match = re.search(r'SD\d+', filename)
            if match:
                return match.group()
        
        # Otherwise, extract everything before "WOB"
        if 'WOB' in filename:
            return filename.split('WOB')[0].strip()
        
        return 'Unknown'