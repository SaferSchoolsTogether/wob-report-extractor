import pdfplumber
import re
import os
import logging
from datetime import datetime

class SmartExtractor:
    def __init__(self, config_manager, debug_mode=False):
        self.config = config_manager
        self.debug_mode = debug_mode
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
        
        # Initialize extraction statistics
        self.extraction_stats = {
            'total_records': 0,
            'field_extraction_counts': {},
            'field_missing_counts': {},
            'extraction_warnings': []
        }
        
        # Set up logging
        self.setup_logging()
    
    def setup_logging(self):
        """Set up logging configuration for error tracking"""
        # Create logs directory if it doesn't exist
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Configure logging
        log_filename = os.path.join(log_dir, f'wob_extractor_{datetime.now().strftime("%Y%m%d")}.log')
        
        # Create logger
        self.logger = logging.getLogger('WOBExtractor')
        self.logger.setLevel(logging.DEBUG)
        
        # Create file handler
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.DEBUG)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        if not self.logger.handlers:  # Avoid adding duplicate handlers
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def extract_from_pdf(self, pdf_path):
        results = {
            'file_name': os.path.basename(pdf_path),
            'records': []
        }
        
        try:
            self.logger.info(f"Processing PDF: {pdf_path}")
            
            with pdfplumber.open(pdf_path) as pdf:
                # Check if PDF is encrypted/locked
                if hasattr(pdf, 'is_encrypted') and pdf.is_encrypted:
                    error_msg = f"PDF is password-protected/encrypted: {os.path.basename(pdf_path)}"
                    self.logger.error(error_msg)
                    results['error'] = error_msg
                    results['error_type'] = 'locked_pdf'
                    return results
                
                full_text = ""
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            full_text += page_text + "\n"
                        else:
                            self.logger.warning(f"No text extracted from page {page_num} in {os.path.basename(pdf_path)}")
                    except Exception as page_error:
                        self.logger.error(f"Error extracting page {page_num} from {os.path.basename(pdf_path)}: {str(page_error)}")
                
                if not full_text.strip():
                    error_msg = f"No text could be extracted from PDF: {os.path.basename(pdf_path)}"
                    self.logger.warning(error_msg)
                    results['error'] = error_msg
                    results['error_type'] = 'no_text'
                    return results
                
                # Extract records
                records = self.extract_records(full_text)
                results['records'] = records
                
                self.logger.info(f"Successfully extracted {len(records)} records from {os.path.basename(pdf_path)}")
                
        except PermissionError as e:
            error_msg = f"Permission denied - PDF may be locked or in use: {os.path.basename(pdf_path)}"
            self.logger.error(error_msg)
            results['error'] = error_msg
            results['error_type'] = 'permission_denied'
            
        except ValueError as e:
            # This often occurs with password-protected PDFs
            if 'password' in str(e).lower() or 'encrypted' in str(e).lower():
                error_msg = f"PDF is password-protected: {os.path.basename(pdf_path)}"
                self.logger.error(error_msg)
                results['error'] = error_msg
                results['error_type'] = 'locked_pdf'
            else:
                error_msg = f"Value error processing PDF {os.path.basename(pdf_path)}: {str(e)}"
                self.logger.error(error_msg)
                results['error'] = error_msg
                results['error_type'] = 'value_error'
                
        except Exception as e:
            error_msg = f"Unexpected error processing {os.path.basename(pdf_path)}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)  # Include full traceback in log
            results['error'] = error_msg
            results['error_type'] = 'general_error'
            
        return results
    
    def extract_records(self, text):
        records = []
        
        try:
            # Split by SOC patterns
            soc_pattern = r'Subject of Concern.*?:|SOC:|Subject:'
            sections = re.split(soc_pattern, text)
            
            for section in sections[1:]:  # Skip first empty section
                record = self.extract_record_from_section(section)
                if record and record.get('name'):
                    records.append(record)
                    
        except Exception as e:
            self.logger.error(f"Error extracting records from text: {str(e)}")
        
        return records
    
    def clean_extracted_text(self, text):
        """Clean extracted text by removing PDF formatting characters like trailing periods, underscores, etc."""
        if not text:
            return text
        
        # Remove trailing periods, dots, underscores, dashes, and spaces
        # Pattern matches: multiple periods, dots (·), underscores, dashes, or spaces at the end
        cleaned = re.sub(r'[\.\·_\-\s]+$', '', text)
        
        # Also remove these characters if they appear in sequences in the middle
        # but only if they're clearly separators (3 or more in a row)
        cleaned = re.sub(r'[\.\·]{3,}', '', cleaned)
        cleaned = re.sub(r'[_]{3,}', '', cleaned)
        cleaned = re.sub(r'[-]{3,}', '', cleaned)
        
        # Clean up any resulting multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()
    
    def extract_record_from_section(self, section):
        record = {}
        missing_fields = []
        
        try:
            self.extraction_stats['total_records'] += 1
            
            # Extract name (first line after SOC:)
            lines = section.strip().split('\n')
            if lines and lines[0].strip():
                # Clean the extracted name to remove formatting characters
                raw_name = lines[0].strip()
                record['name'] = self.clean_extracted_text(raw_name)
                self._track_field_extraction('name', True)
                if self.debug_mode:
                    if raw_name != record['name']:
                        self.logger.debug(f"Cleaned name from '{raw_name}' to '{record['name']}'")
                    else:
                        self.logger.debug(f"Extracted name: {record['name']}")
            else:
                missing_fields.append('name')
                self._track_field_extraction('name', False)
                self.logger.warning(f"Failed to extract name from section starting with: {section[:100]}")
            
            # Extract SOC affiliation with multiple patterns
            soc_affiliation_patterns = [
                r'SOC Affiliation:\s*(.+?)(?:\n|$)',
                r'Affiliation:\s*(.+?)(?:\n|$)',
                r'Gang Affiliation:\s*(.+?)(?:\n|$)',
                r'Group Affiliation:\s*(.+?)(?:\n|$)'
            ]
            soc_affiliation_found = False
            for pattern in soc_affiliation_patterns:
                soc_match = re.search(pattern, section, re.IGNORECASE)
                if soc_match:
                    # Clean the extracted SOC affiliation
                    raw_affiliation = soc_match.group(1).strip()
                    record['soc_affiliation'] = self.clean_extracted_text(raw_affiliation)
                    soc_affiliation_found = True
                    self._track_field_extraction('soc_affiliation', True)
                    if self.debug_mode:
                        if raw_affiliation != record['soc_affiliation']:
                            self.logger.debug(f"Cleaned SOC affiliation from '{raw_affiliation}' to '{record['soc_affiliation']}' using pattern: {pattern}")
                        else:
                            self.logger.debug(f"Extracted SOC affiliation: {record['soc_affiliation']} using pattern: {pattern}")
                    break
            
            if not soc_affiliation_found:
                # Not all records have SOC affiliation, so we don't add to missing_fields
                # but we still track it
                record['soc_affiliation'] = ''
                self._track_field_extraction('soc_affiliation', False)
                if self.debug_mode:
                    self.logger.debug(f"No SOC affiliation found in section")
            
            # Extract location with multiple patterns
            location_patterns = [
                r'Location:\s*(.+?)(?:\n|$)',
                r'City/Town:\s*(.+?)(?:\n|$)',
                r'Municipality:\s*(.+?)(?:\n|$)'
            ]
            location_found = False
            for pattern in location_patterns:
                location_match = re.search(pattern, section, re.IGNORECASE)
                if location_match:
                    # Clean the extracted location
                    raw_location = location_match.group(1).strip()
                    record['location'] = self.clean_extracted_text(raw_location)
                    location_found = True
                    self._track_field_extraction('location', True)
                    if self.debug_mode:
                        if raw_location != record['location']:
                            self.logger.debug(f"Cleaned location from '{raw_location}' to '{record['location']}' using pattern: {pattern}")
                        else:
                            self.logger.debug(f"Extracted location: {record['location']} using pattern: {pattern}")
                    break
            
            if not location_found:
                missing_fields.append('location')
                self._track_field_extraction('location', False)
                if self.debug_mode:
                    self.logger.debug(f"No location found in section. Searched text: {section[:200]}")
            
            # Extract school with multiple patterns
            school_patterns = [
                r'School.*?:\s*(.+?)(?:\n|$)',
                r'Institution:\s*(.+?)(?:\n|$)',
                r'School Name:\s*(.+?)(?:\n|$)'
            ]
            school_found = False
            for pattern in school_patterns:
                school_match = re.search(pattern, section, re.IGNORECASE)
                if school_match:
                    # Clean the extracted school name
                    raw_school = school_match.group(1).strip()
                    record['school'] = self.clean_extracted_text(raw_school)
                    school_found = True
                    self._track_field_extraction('school', True)
                    if self.debug_mode:
                        if raw_school != record['school']:
                            self.logger.debug(f"Cleaned school from '{raw_school}' to '{record['school']}' using pattern: {pattern}")
                        else:
                            self.logger.debug(f"Extracted school: {record['school']} using pattern: {pattern}")
                    break
            
            if not school_found:
                missing_fields.append('school')
                self._track_field_extraction('school', False)
                if self.debug_mode:
                    self.logger.debug(f"No school found in section. Searched text: {section[:200]}")
            
            # Extract concerns
            record['concerns'] = {}
            concerns_found = 0
            for concern in self.concern_categories:
                # Check if concern is marked
                if self.is_concern_checked(section, concern):
                    record['concerns'][concern] = True
                    concerns_found += 1
                elif self.is_concern_unchecked(section, concern):
                    record['concerns'][concern] = False
            
            # Check for "Other" concern with custom text
            other_patterns = [
                r'☒\s*Other:\s*(.+?)(?:\n|$)',
                r'\[X\]\s*Other:\s*(.+?)(?:\n|$)',
                r'✓\s*Other:\s*(.+?)(?:\n|$)'
            ]
            
            record['other_concern'] = False
            record['other_concern_text'] = ''
            
            for pattern in other_patterns:
                other_match = re.search(pattern, section, re.IGNORECASE)
                if other_match:
                    record['other_concern'] = True
                    record['other_concern_text'] = self.clean_extracted_text(other_match.group(1))
                    concerns_found += 1
                    if self.debug_mode:
                        self.logger.debug(f"Found 'Other' concern: {record['other_concern_text']}")
                    break
            
            # If Other not checked, look for unchecked pattern
            if not record['other_concern']:
                unchecked_other_patterns = [
                    r'☐\s*Other:',
                    r'\[\s\]\s*Other:'
                ]
                for pattern in unchecked_other_patterns:
                    if re.search(pattern, section, re.IGNORECASE):
                        record['other_concern'] = False
                        break
            
            if concerns_found == 0:
                missing_fields.append('concerns')
                self._track_field_extraction('concerns', False)
                self.logger.warning(f"No concerns found for record: {record.get('name', 'Unknown')}")
            else:
                self._track_field_extraction('concerns', True)
                if self.debug_mode:
                    self.logger.debug(f"Found {concerns_found} concerns marked")
            
            # Extract social media
            record['social_media'] = self.extract_social_media(section)
            if record['social_media']:
                self._track_field_extraction('social_media', True)
            else:
                self._track_field_extraction('social_media', False)
            
            # Log extraction quality warning if fields are missing
            if missing_fields:
                warning_msg = f"Record '{record.get('name', 'Unknown')}' has missing fields: {', '.join(missing_fields)}"
                self.extraction_stats['extraction_warnings'].append(warning_msg)
                self.logger.warning(warning_msg)
            
        except Exception as e:
            self.logger.error(f"Error extracting record from section: {str(e)}", exc_info=True)
        
        return record
    
    def _track_field_extraction(self, field_name, success):
        """Track field extraction success/failure statistics"""
        if field_name not in self.extraction_stats['field_extraction_counts']:
            self.extraction_stats['field_extraction_counts'][field_name] = 0
            self.extraction_stats['field_missing_counts'][field_name] = 0
        
        if success:
            self.extraction_stats['field_extraction_counts'][field_name] += 1
        else:
            self.extraction_stats['field_missing_counts'][field_name] += 1
    
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
        
        try:
            # Look for social media sections - updated pattern to be more flexible
            sm_patterns = [
                r'(Instagram|TikTok|Snapchat|Facebook|Twitter|Discord|YouTube|Reddit|Telegram|WhatsApp).*?Information.*?Activity',
                r'(Instagram|TikTok|Snapchat|Facebook|Twitter|Discord|YouTube|Reddit|Telegram|WhatsApp)\s+(?:Display\s+)?Name:',
                r'(Instagram|TikTok|Snapchat|Facebook|Twitter|Discord|YouTube|Reddit|Telegram|WhatsApp)\s+Username:'
            ]
            
            # Try each pattern
            sm_sections = []
            for pattern in sm_patterns:
                temp_sections = re.split(pattern, section, flags=re.IGNORECASE)
                if len(temp_sections) > 1:
                    sm_sections = temp_sections
                    break
            
            # If no sections found, try to find individual platform mentions
            if len(sm_sections) <= 1:
                # Look for individual platform data
                platforms = ['Instagram', 'TikTok', 'Snapchat', 'Facebook', 'Twitter', 
                           'Discord', 'YouTube', 'Reddit', 'Telegram', 'WhatsApp']
                
                for platform in platforms:
                    # Check if platform data exists in section
                    platform_pattern = f'{platform}.*?(?:Display Name|Username|ID|URL):'
                    if re.search(platform_pattern, section, re.IGNORECASE):
                        sm_data = self.extract_platform_data(section, platform)
                        if sm_data:
                            social_media.append(sm_data)
            else:
                # Process sections as before
                for i in range(1, len(sm_sections), 2):
                    platform = sm_sections[i]
                    content = sm_sections[i+1] if i+1 < len(sm_sections) else ""
                    
                    # Combine with remaining text if needed
                    if i+1 < len(sm_sections):
                        # Get text until next platform or end
                        next_platform_idx = len(content)
                        for p in ['Instagram', 'TikTok', 'Snapchat', 'Facebook', 'Twitter', 
                                'Discord', 'YouTube', 'Reddit', 'Telegram', 'WhatsApp']:
                            pattern = f'{p}.*?(?:Information|Display Name|Username):'
                            match = re.search(pattern, content, re.IGNORECASE)
                            if match:
                                next_platform_idx = min(next_platform_idx, match.start())
                        content = content[:next_platform_idx]
                    
                    sm_data = self.extract_platform_data(content, platform)
                    if sm_data:
                        social_media.append(sm_data)
                    
        except Exception as e:
            self.logger.warning(f"Error extracting social media data: {str(e)}")
        
        return social_media
    
    def extract_platform_data(self, content, platform):
        """Extract social media data for a specific platform"""
        sm_data = {'platform': platform}
        
        try:
            # Extract Display Name
            display_patterns = [
                f'{platform}\\s+Display\\s+Name:\\s*(.+?)(?:\\n|$)',
                f'Display\\s+Name:\\s*(.+?)(?:\\n|$)'
            ]
            for pattern in display_patterns:
                display_match = re.search(pattern, content, re.IGNORECASE)
                if display_match:
                    raw_display = display_match.group(1).strip()
                    sm_data['display_name'] = self.clean_extracted_text(raw_display)
                    break
            
            # Extract Username
            username_patterns = [
                f'{platform}\\s+Username:\\s*(.+?)(?:\\n|$)',
                f'Username:\\s*(.+?)(?:\\n|$)',
                f'@(.+?)(?:\\s|\\n|$)'  # Handle @username format
            ]
            for pattern in username_patterns:
                username_match = re.search(pattern, content, re.IGNORECASE)
                if username_match:
                    raw_username = username_match.group(1).strip()
                    # Remove @ if present at start
                    raw_username = raw_username.lstrip('@')
                    sm_data['username'] = self.clean_extracted_text(raw_username)
                    break
            
            # Extract User ID (platform-specific ID number)
            id_patterns = [
                f'{platform}\\s+ID:\\s*(.+?)(?:\\n|$)',
                f'{platform}\\s+User\\s+ID:\\s*(.+?)(?:\\n|$)',
                f'ID:\\s*(.+?)(?:\\n|$)',
                f'User\\s+ID:\\s*(.+?)(?:\\n|$)'
            ]
            for pattern in id_patterns:
                id_match = re.search(pattern, content, re.IGNORECASE)
                if id_match:
                    raw_id = id_match.group(1).strip()
                    # Clean but preserve numbers
                    cleaned_id = re.sub(r'[^\d\w\-_]', '', raw_id)
                    if cleaned_id:
                        sm_data['user_id'] = cleaned_id
                        break
            
            # Extract URL
            url_patterns = [
                f'{platform}\\s+URL:\\s*(.+?)(?:\\n|$)',
                f'URL:\\s*(.+?)(?:\\n|$)',
                r'(https?://(?:www\.)?(?:instagram|tiktok|snapchat|facebook|twitter|discord|youtube|reddit|telegram|whatsapp)[^\s]+)'
            ]
            for pattern in url_patterns:
                url_match = re.search(pattern, content, re.IGNORECASE)
                if url_match:
                    raw_url = url_match.group(1).strip()
                    # Remove only trailing formatting characters
                    cleaned_url = re.sub(r'[\.\·_\-\s]+$', '', raw_url)
                    sm_data['url'] = cleaned_url
                    break
            
            # Only return if we have at least one field besides platform
            if len(sm_data) > 1:
                return sm_data
                
        except Exception as e:
            self.logger.warning(f"Error extracting {platform} data: {str(e)}")
        
        return None
    
    def get_error_summary(self):
        """Get a summary of errors from the log file"""
        summary = {
            'locked_pdfs': [],
            'permission_errors': [],
            'other_errors': []
        }
        
        try:
            log_filename = os.path.join('logs', f'wob_extractor_{datetime.now().strftime("%Y%m%d")}.log')
            if os.path.exists(log_filename):
                with open(log_filename, 'r') as f:
                    for line in f:
                        if 'password-protected' in line.lower() or 'encrypted' in line.lower():
                            summary['locked_pdfs'].append(line.strip())
                        elif 'permission denied' in line.lower():
                            summary['permission_errors'].append(line.strip())
                        elif 'ERROR' in line:
                            summary['other_errors'].append(line.strip())
        except Exception as e:
            self.logger.error(f"Error reading log file: {str(e)}")
        
        return summary
    
    def get_extraction_quality_report(self):
        """Generate a detailed extraction quality report"""
        report = {
            'total_records_processed': self.extraction_stats['total_records'],
            'field_success_rates': {},
            'missing_data_summary': {},
            'extraction_warnings': self.extraction_stats['extraction_warnings'][:20],  # First 20 warnings
            'recommendations': []
        }
        
        # Calculate success rates for each field
        for field in self.extraction_stats['field_extraction_counts']:
            success_count = self.extraction_stats['field_extraction_counts'][field]
            missing_count = self.extraction_stats['field_missing_counts'][field]
            total = success_count + missing_count
            
            if total > 0:
                success_rate = (success_count / total) * 100
                report['field_success_rates'][field] = {
                    'success_rate': f"{success_rate:.1f}%",
                    'successful': success_count,
                    'missing': missing_count,
                    'total': total
                }
                
                # Add to missing data summary if there are failures
                if missing_count > 0:
                    report['missing_data_summary'][field] = {
                        'missing_count': missing_count,
                        'percentage': f"{(missing_count / total) * 100:.1f}%"
                    }
        
        # Generate recommendations based on extraction quality
        if report['missing_data_summary']:
            for field, stats in report['missing_data_summary'].items():
                missing_pct = float(stats['percentage'].rstrip('%'))
                if missing_pct > 50:
                    report['recommendations'].append(
                        f"Critical: {field} field missing in {stats['percentage']} of records. "
                        f"Check PDF format or update extraction patterns."
                    )
                elif missing_pct > 20:
                    report['recommendations'].append(
                        f"Warning: {field} field missing in {stats['percentage']} of records. "
                        f"Consider reviewing extraction logic."
                    )
        
        if not report['recommendations']:
            report['recommendations'].append("Extraction quality is good. All fields extracting successfully.")
        
        return report
    
    def reset_extraction_stats(self):
        """Reset extraction statistics for a new batch"""
        self.extraction_stats = {
            'total_records': 0,
            'field_extraction_counts': {},
            'field_missing_counts': {},
            'extraction_warnings': []
        }
        self.logger.info("Extraction statistics reset")
    
    def save_extraction_quality_report(self, output_folder, month_year):
        """Save extraction quality report to a CSV file"""
        try:
            report = self.get_extraction_quality_report()
            timestamp = datetime.now().strftime("%Y%m%d")
            
            # Create quality report data for CSV
            quality_data = []
            
            # Add field success rates
            for field, stats in report['field_success_rates'].items():
                quality_data.append({
                    'Report Section': 'Field Success Rates',
                    'Field': field,
                    'Success Rate': stats['success_rate'],
                    'Successful Extractions': stats['successful'],
                    'Missing Data': stats['missing'],
                    'Total Records': stats['total']
                })
            
            # Add warnings (first 10)
            for warning in report['extraction_warnings'][:10]:
                quality_data.append({
                    'Report Section': 'Extraction Warnings',
                    'Field': '',
                    'Success Rate': '',
                    'Successful Extractions': '',
                    'Missing Data': '',
                    'Total Records': '',
                    'Warning': warning
                })
            
            # Add recommendations
            for rec in report['recommendations']:
                quality_data.append({
                    'Report Section': 'Recommendations',
                    'Field': '',
                    'Success Rate': '',
                    'Successful Extractions': '',
                    'Missing Data': '',
                    'Total Records': '',
                    'Recommendation': rec
                })
            
            if quality_data:
                import pandas as pd
                df = pd.DataFrame(quality_data)
                quality_file = os.path.join(output_folder, f"{timestamp} - Extraction Quality Report ({month_year}).csv")
                df.to_csv(quality_file, index=False)
                self.logger.info(f"Extraction quality report saved to: {quality_file}")
                return quality_file
            
        except Exception as e:
            self.logger.error(f"Error saving extraction quality report: {str(e)}")
            return None
