import pdfplumber
import re
import os

class SmartExtractor:
    def __init__(self, config_manager):
        self.config = config_manager
        self.concern_categories = [
            'Mental Health Concerns', 'Firearms', 'Weapons',
            'Threat-Related Behavior', 'Physical Violence',
            'Substance Use Concerns', 'Suicidal Ideation',
            'Gang-Associated Behavior', 'Bullying/Cyberbullying',
            'School Community Concerns', 'Risk of Sextortion',
            'Sexual Assault', 'Non-Suicidal Self-Harm',
            'Negative Digital Climate/Culture', 'Hate/Racism or Radicalization',
            'Illegal Activity Misc.', 'Passed Away'
        ]
    
    def extract_from_pdf(self, pdf_path):
        results = {
            'file_name': os.path.basename(pdf_path),
            'records': []
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                
                # Extract records
                records = self.extract_records(full_text)
                results['records'] = records
                
        except Exception as e:
            results['error'] = str(e)
            
        return results
    
    def extract_records(self, text):
        records = []
        
        # Split by SOC patterns
        soc_pattern = r'Subject of Concern.*?:|SOC:|Subject:'
        sections = re.split(soc_pattern, text)
        
        for section in sections[1:]:  # Skip first empty section
            record = self.extract_record_from_section(section)
            if record and record.get('name'):
                records.append(record)
        
        return records
    
    def extract_record_from_section(self, section):
        record = {}
        
        # Extract name (first line after SOC:)
        lines = section.strip().split('\n')
        if lines:
            record['name'] = lines[0].strip()
        
        # Extract location
        location_match = re.search(r'Location:\s*(.+?)(?:\n|$)', section)
        if location_match:
            record['location'] = location_match.group(1).strip()
        
        # Extract school
        school_match = re.search(r'School.*?:\s*(.+?)(?:\n|$)', section)
        if school_match:
            record['school'] = school_match.group(1).strip()
        
        # Extract concerns
        record['concerns'] = {}
        for concern in self.concern_categories:
            # Check if concern is marked
            if self.is_concern_checked(section, concern):
                record['concerns'][concern] = True
            elif self.is_concern_unchecked(section, concern):
                record['concerns'][concern] = False
        
        # Extract social media
        record['social_media'] = self.extract_social_media(section)
        
        return record
    
    def is_concern_checked(self, text, concern):
        patterns = [
            f'☒\\s*{re.escape(concern)}',
            f'\\[X\\]\\s*{re.escape(concern)}',
            f'✓\\s*{re.escape(concern)}'
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Also check for table format (Dodge County style)
        table_pattern = f'{re.escape(concern)}.*?\\|.*?X'
        if re.search(table_pattern, text, re.IGNORECASE):
            return True
            
        return False
    
    def is_concern_unchecked(self, text, concern):
        patterns = [
            f'☐\\s*{re.escape(concern)}',
            f'\\[\\s\\]\\s*{re.escape(concern)}'
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def extract_social_media(self, section):
        social_media = []
        
        # Look for social media sections
        sm_pattern = r'(Instagram|TikTok|Snapchat|Facebook|Twitter|Discord).*?Information.*?Activity'
        sm_sections = re.split(sm_pattern, section, flags=re.IGNORECASE)
        
        for i in range(1, len(sm_sections), 2):
            platform = sm_sections[i]
            content = sm_sections[i+1] if i+1 < len(sm_sections) else ""
            
            sm_data = {'platform': platform}
            
            # Extract username
            username_match = re.search(r'Username:\s*(.+?)(?:\n|$)', content)
            if username_match:
                sm_data['username'] = username_match.group(1).strip()
            
            # Extract URL
            url_match = re.search(r'URL:\s*(.+?)(?:\n|$)', content)
            if url_match:
                sm_data['url'] = url_match.group(1).strip()
                
            if sm_data.get('username') or sm_data.get('url'):
                social_media.append(sm_data)
        
        return social_media