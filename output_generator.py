import pandas as pd
import os
import re
from datetime import datetime
from collections import Counter

class OutputGenerator:
    def generate_reports(self, extracted_data, output_folder, month_year):
        timestamp = datetime.now().strftime("%Y%m%d")
        
        # Initialize data collections
        social_media_data = []
        concerns_data = []
        platform_stats = Counter()
        soc_with_multiple_accounts = {}
        total_socs = 0
        
        # Process all extracted data
        for file_data in extracted_data:
            if 'error' not in file_data:
                district = self.extract_district(file_data['file_name'])
                
                for record in file_data.get('records', []):
                    total_socs += 1
                    soc_name = record.get('name', '')
                    
                    # Track SOCs with multiple accounts
                    if soc_name not in soc_with_multiple_accounts:
                        soc_with_multiple_accounts[soc_name] = 0
                    
                    # 1. Process Social Media Data (with duplication per account)
                    social_media_accounts = record.get('social_media', [])
                    
                    if social_media_accounts:
                        for sm in social_media_accounts:
                            platform = sm.get('platform', '')
                            if platform:
                                platform_stats[platform] += 1
                                soc_with_multiple_accounts[soc_name] += 1
                            
                            social_media_data.append({
                                'SOC_Name': soc_name,
                                'District': district,
                                'School': record.get('school', ''),
                                'Location': record.get('location', ''),
                                'SOC_Affiliation': record.get('soc_affiliation', ''),
                                'Platform': platform,
                                'Display_Name': sm.get('display_name', ''),
                                'Username': sm.get('username', ''),
                                'User_ID': sm.get('user_id', ''),
                                'URL': sm.get('url', '')
                            })
                    else:
                        # Add record even if no social media (with empty social media fields)
                        social_media_data.append({
                            'SOC_Name': soc_name,
                            'District': district,
                            'School': record.get('school', ''),
                            'Location': record.get('location', ''),
                            'SOC_Affiliation': record.get('soc_affiliation', ''),
                            'Platform': '',
                            'Display_Name': '',
                            'Username': '',
                            'User_ID': '',
                            'URL': ''
                        })
                    
                    # 2. Process Concerns Data
                    concern_row = {
                        'SOC_Name': soc_name,
                        'District': district,
                        'School': record.get('school', ''),
                        'Location': record.get('location', ''),
                        'SOC_Affiliation': record.get('soc_affiliation', '')
                    }
                    
                    # Add all standard concern categories as columns
                    all_concerns = record.get('concerns', {})
                    for concern_name, is_checked in all_concerns.items():
                        concern_row[concern_name] = 1 if is_checked else 0
                    
                    # Add "Other" concern columns
                    concern_row['Other'] = 1 if record.get('other_concern', False) else 0
                    concern_row['Other_Text'] = record.get('other_concern_text', '')
                    
                    concerns_data.append(concern_row)
        
        # Generate CSV files
        files_created = []
        
        # 1. Social Media Data CSV
        if social_media_data:
            sm_df = pd.DataFrame(social_media_data)
            sm_file = os.path.join(output_folder, f"{timestamp} - Social Media Data ({month_year}).csv")
            sm_df.to_csv(sm_file, index=False)
            files_created.append(('Social Media Data', len(social_media_data), sm_file))
        
        # 2. Concerns Summary CSV
        if concerns_data:
            concerns_df = pd.DataFrame(concerns_data)
            concerns_file = os.path.join(output_folder, f"{timestamp} - WOB Concerns Data ({month_year}).csv")
            concerns_df.to_csv(concerns_file, index=False)
            files_created.append(('Concerns Data', len(concerns_data), concerns_file))
        
        # 3. Generate Social Media Analytics Summary
        analytics_data = self.generate_analytics_summary(
            platform_stats, 
            soc_with_multiple_accounts, 
            total_socs,
            month_year,
            output_folder,
            timestamp
        )
        
        if analytics_data:
            files_created.append(('Analytics Summary', 1, analytics_data))
        
        # 4. Also generate legacy Account Tracker for backward compatibility (optional)
        account_data = []
        for file_data in extracted_data:
            if 'error' not in file_data:
                for record in file_data.get('records', []):
                    base_info = {
                        'month': month_year,
                        'district': self.extract_district(file_data['file_name']),
                        'entity_nam': record.get('name', ''),
                        'school': record.get('school', ''),
                        'soc_affiliation': record.get('soc_affiliation', ''),
                        'concerns': ', '.join([k for k, v in record.get('concerns', {}).items() if v])
                    }
                    
                    # Add social media records
                    for sm in record.get('social_media', []):
                        sm_record = base_info.copy()
                        sm_record.update({
                            'sm_typ': sm.get('platform', ''),
                            'us': sm.get('username', ''),
                            'user_id': sm.get('user_id', ''),  # Added user ID
                            'url': sm.get('url', '')
                        })
                        account_data.append(sm_record)
                    
                    # If no social media, still add the record
                    if not record.get('social_media'):
                        base_info.update({'sm_typ': '', 'us': '', 'user_id': '', 'url': ''})
                        account_data.append(base_info)
        
        if account_data:
            account_df = pd.DataFrame(account_data)
            account_file = os.path.join(output_folder, f"{timestamp} - Account Tracker ({month_year}).csv")
            account_df.to_csv(account_file, index=False)
            files_created.append(('Account Tracker (Legacy)', len(account_data), account_file))
        
        return files_created, platform_stats
    
    def generate_analytics_summary(self, platform_stats, soc_with_multiple_accounts, 
                                  total_socs, month_year, output_folder, timestamp):
        """Generate a summary report with social media analytics"""
        try:
            summary_lines = []
            summary_lines.append(f"WOB Report Analytics Summary - {month_year}")
            summary_lines.append("=" * 60)
            summary_lines.append("")
            
            # Overall statistics
            summary_lines.append("OVERALL STATISTICS")
            summary_lines.append("-" * 30)
            summary_lines.append(f"Total Subjects of Concern: {total_socs}")
            summary_lines.append(f"Total Social Media Accounts: {sum(platform_stats.values())}")
            summary_lines.append("")
            
            # Platform distribution
            if platform_stats:
                summary_lines.append("SOCIAL MEDIA PLATFORM DISTRIBUTION")
                summary_lines.append("-" * 30)
                
                total_accounts = sum(platform_stats.values())
                sorted_platforms = sorted(platform_stats.items(), key=lambda x: x[1], reverse=True)
                
                for platform, count in sorted_platforms:
                    percentage = (count / total_accounts) * 100 if total_accounts > 0 else 0
                    summary_lines.append(f"{platform:15} {count:4} accounts ({percentage:5.1f}%)")
                
                summary_lines.append("")
                
                # Most active platform
                if sorted_platforms:
                    most_active = sorted_platforms[0]
                    summary_lines.append(f"Most Active Platform: {most_active[0]} with {most_active[1]} accounts")
                    summary_lines.append("")
            
            # SOCs with multiple accounts
            multi_account_socs = [(name, count) for name, count in soc_with_multiple_accounts.items() if count > 1]
            if multi_account_socs:
                summary_lines.append("SUBJECTS WITH MULTIPLE SOCIAL MEDIA ACCOUNTS")
                summary_lines.append("-" * 30)
                
                sorted_multi = sorted(multi_account_socs, key=lambda x: x[1], reverse=True)[:10]  # Top 10
                for name, count in sorted_multi:
                    summary_lines.append(f"{name}: {count} accounts")
                
                if len(multi_account_socs) > 10:
                    summary_lines.append(f"... and {len(multi_account_socs) - 10} more SOCs with multiple accounts")
                
                summary_lines.append("")
            
            # Platform comparison for analysis
            summary_lines.append("PLATFORM ACTIVITY ANALYSIS")
            summary_lines.append("-" * 30)
            
            # TikTok vs Instagram comparison (as requested)
            tiktok_count = platform_stats.get('TikTok', 0)
            instagram_count = platform_stats.get('Instagram', 0)
            
            if tiktok_count > 0 or instagram_count > 0:
                total_ti = tiktok_count + instagram_count
                if total_ti > 0:
                    summary_lines.append(f"TikTok vs Instagram:")
                    summary_lines.append(f"  TikTok:    {tiktok_count:4} accounts ({(tiktok_count/total_ti)*100:5.1f}% of TikTok+Instagram)")
                    summary_lines.append(f"  Instagram: {instagram_count:4} accounts ({(instagram_count/total_ti)*100:5.1f}% of TikTok+Instagram)")
            
            # Save summary to file
            summary_file = os.path.join(output_folder, f"{timestamp} - Analytics Summary ({month_year}).txt")
            with open(summary_file, 'w') as f:
                f.write('\n'.join(summary_lines))
            
            # Also create a CSV version for easier analysis
            analytics_csv_data = []
            
            # Platform statistics for CSV
            for platform, count in platform_stats.items():
                percentage = (count / sum(platform_stats.values())) * 100 if platform_stats else 0
                analytics_csv_data.append({
                    'Category': 'Platform Statistics',
                    'Item': platform,
                    'Count': count,
                    'Percentage': f"{percentage:.1f}%"
                })
            
            # SOCs with multiple accounts for CSV
            for name, count in multi_account_socs[:20]:  # Top 20 for CSV
                analytics_csv_data.append({
                    'Category': 'Multiple Accounts',
                    'Item': name,
                    'Count': count,
                    'Percentage': ''
                })
            
            if analytics_csv_data:
                analytics_df = pd.DataFrame(analytics_csv_data)
                analytics_csv_file = os.path.join(output_folder, f"{timestamp} - Analytics Data ({month_year}).csv")
                analytics_df.to_csv(analytics_csv_file, index=False)
            
            return summary_file
            
        except Exception as e:
            print(f"Error generating analytics summary: {str(e)}")
            return None
    
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
