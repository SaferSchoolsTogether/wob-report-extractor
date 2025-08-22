import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from datetime import datetime
from config_manager import ConfigManager
from extractor_engine import SmartExtractor
from output_generator import OutputGenerator

class WOBExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WOB Report Extractor")
        self.root.geometry("700x650")
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.debug_mode = False  # Can be toggled via UI
        self.extractor = SmartExtractor(self.config_manager, debug_mode=self.debug_mode)
        self.output_gen = OutputGenerator()
        
        self.selected_folder = None
        
        # Create UI
        self.create_widgets()
        
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.root, bg='navy', pady=20)
        title_frame.pack(fill='x')
        
        title = tk.Label(title_frame, text="WOB Report Data Extractor", 
                        font=("Arial", 20, "bold"), fg='white', bg='navy')
        title.pack()
        
        # Instructions
        instructions = tk.Label(self.root, text="Extract data from WOB PDF reports in 3 easy steps!",
                              font=("Arial", 12), pady=10)
        instructions.pack()
        
        # Step 1: Select folder
        step1_frame = tk.Frame(self.root, pady=20)
        step1_frame.pack()
        
        tk.Label(step1_frame, text="Step 1:", font=("Arial", 12, "bold")).pack()
        self.select_btn = tk.Button(
            step1_frame, 
            text="📁 Select Folder with PDF Reports",
            command=self.select_folder,
            bg="#4CAF50", fg="white", font=("Arial", 11),
            padx=20, pady=10, cursor="hand2"
        )
        self.select_btn.pack(pady=5)
        
        self.folder_label = tk.Label(step1_frame, text="No folder selected", fg="gray")
        self.folder_label.pack()
        
        # Step 2: Select month/year
        step2_frame = tk.Frame(self.root, pady=20)
        step2_frame.pack()
        
        tk.Label(step2_frame, text="Step 2: Select Month and Year", font=("Arial", 12, "bold")).pack(pady=5)
        
        date_frame = tk.Frame(step2_frame)
        date_frame.pack()
        
        tk.Label(date_frame, text="Month:").grid(row=0, column=0, padx=5)
        self.month_var = ttk.Combobox(date_frame, values=[
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ], width=15)
        self.month_var.grid(row=0, column=1, padx=5)
        self.month_var.set(datetime.now().strftime("%B"))
        
        tk.Label(date_frame, text="Year:").grid(row=0, column=2, padx=5)
        self.year_var = ttk.Combobox(date_frame, values=[
            "2024", "2025", "2026"
        ], width=10)
        self.year_var.grid(row=0, column=3, padx=5)
        self.year_var.set(datetime.now().strftime("%Y"))
        
        # Step 3: Process
        step3_frame = tk.Frame(self.root, pady=20)
        step3_frame.pack()
        
        tk.Label(step3_frame, text="Step 3:", font=("Arial", 12, "bold")).pack()
        
        # Add debug mode checkbox
        self.debug_var = tk.BooleanVar()
        debug_checkbox = tk.Checkbutton(
            step3_frame,
            text="Enable Debug Mode (detailed logging)",
            variable=self.debug_var,
            command=self.toggle_debug_mode
        )
        debug_checkbox.pack(pady=5)
        
        self.process_btn = tk.Button(
            step3_frame,
            text="🚀 Extract Data from Reports",
            command=self.process_reports,
            bg="#2196F3", fg="white", font=("Arial", 11, "bold"),
            padx=20, pady=10, cursor="hand2",
            state="disabled"
        )
        self.process_btn.pack(pady=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.root, length=500, mode='determinate')
        self.progress.pack(pady=10)
        
        # Status text
        status_frame = tk.Frame(self.root)
        status_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        tk.Label(status_frame, text="Status Log:", font=("Arial", 10, "bold")).pack(anchor='w')
        
        # Add scrollbar to status text
        text_frame = tk.Frame(status_frame)
        text_frame.pack(fill='both', expand=True)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.status_text = tk.Text(text_frame, height=10, width=70, yscrollcommand=scrollbar.set)
        self.status_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.status_text.yview)
        
    def select_folder(self):
        folder = filedialog.askdirectory(title="Select folder containing WOB PDF reports")
        if folder:
            self.selected_folder = folder
            self.folder_label.config(text=f"✓ Selected: {os.path.basename(folder)}", fg="green")
            self.process_btn.config(state="normal")
            self.log(f"Folder selected: {folder}")
    
    def log(self, message):
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.root.update()
    
    def toggle_debug_mode(self):
        """Toggle debug mode for detailed extraction logging"""
        self.debug_mode = self.debug_var.get()
        self.extractor.debug_mode = self.debug_mode
        if self.debug_mode:
            self.log("🔍 Debug mode enabled - detailed logging active")
        else:
            self.log("Debug mode disabled")
    
    def find_pdfs(self, folder, month_year):
        pdf_files = []
        for file in os.listdir(folder):
            if file.endswith('.pdf') and month_year in file:
                pdf_files.append(os.path.join(folder, file))
        return pdf_files
    
    def process_reports(self):
        try:
            # Clear previous status
            self.status_text.delete(1.0, tk.END)
            self.process_btn.config(state="disabled")
            
            # Reset extraction statistics for new batch
            self.extractor.reset_extraction_stats()
            
            # Get selected month/year
            month_year = f"{self.month_var.get()} {self.year_var.get()}"
            
            # Find PDFs
            self.log(f"🔍 Looking for {month_year} reports...")
            pdf_files = self.find_pdfs(self.selected_folder, month_year)
            
            if not pdf_files:
                messagebox.showwarning("No Files", f"No PDF files found for {month_year}")
                self.process_btn.config(state="normal")
                return
                
            self.log(f"📄 Found {len(pdf_files)} PDF files")
            
            # Process each PDF
            self.progress['maximum'] = len(pdf_files)
            self.progress['value'] = 0
            results = []
            locked_pdfs = []
            other_errors = []
            
            for i, pdf in enumerate(pdf_files):
                self.log(f"\n📖 Processing: {os.path.basename(pdf)}")
                result = self.extractor.extract_from_pdf(pdf)
                
                if 'error' in result:
                    error_type = result.get('error_type', 'general_error')
                    if error_type == 'locked_pdf':
                        self.log(f"  🔒 LOCKED PDF: Cannot process (password-protected)")
                        locked_pdfs.append(os.path.basename(pdf))
                    elif error_type == 'permission_denied':
                        self.log(f"  ⛔ Permission Denied: File may be in use")
                        other_errors.append((os.path.basename(pdf), "Permission denied"))
                    elif error_type == 'no_text':
                        self.log(f"  ⚠️ Warning: No text found in PDF")
                        other_errors.append((os.path.basename(pdf), "No text extracted"))
                    else:
                        self.log(f"  ⚠️ Warning: {result['error']}")
                        other_errors.append((os.path.basename(pdf), result['error']))
                else:
                    num_records = len(result.get('records', []))
                    self.log(f"  ✓ Found {num_records} subjects of concern")
                
                results.append(result)
                self.progress['value'] = i + 1
                self.root.update()
            
            # Generate output files
            self.log("\n📊 Generating output files...")
            files_created, platform_stats = self.output_gen.generate_reports(
                results, self.selected_folder, month_year
            )
            
            # Generate and save extraction quality report
            self.log("\n📈 Generating extraction quality report...")
            quality_file = self.extractor.save_extraction_quality_report(self.selected_folder, month_year)
            
            # Get extraction quality summary
            quality_report = self.extractor.get_extraction_quality_report()
            
            # Summary
            self.log(f"\n✅ PROCESSING COMPLETE!")
            self.log(f"\n📁 Files Generated:")
            for file_type, count, filepath in files_created:
                filename = os.path.basename(filepath) if isinstance(filepath, str) else 'Generated'
                self.log(f"  - {file_type}: {count} records → {filename}")
            
            # Display platform statistics
            if platform_stats:
                self.log(f"\n📱 Social Media Platform Distribution:")
                total_accounts = sum(platform_stats.values())
                for platform, count in sorted(platform_stats.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / total_accounts) * 100 if total_accounts > 0 else 0
                    self.log(f"  - {platform}: {count} accounts ({percentage:.1f}%)")
            
            # Display extraction quality metrics
            self.log(f"\n📊 EXTRACTION QUALITY METRICS:")
            self.log(f"  - Total records processed: {quality_report['total_records_processed']}")
            
            if quality_report['field_success_rates']:
                self.log(f"\n  Field Extraction Success Rates:")
                for field, stats in quality_report['field_success_rates'].items():
                    self.log(f"    • {field}: {stats['success_rate']} ({stats['successful']}/{stats['total']})")
            
            if quality_report['missing_data_summary']:
                self.log(f"\n  ⚠️ Fields with Missing Data:")
                for field, stats in quality_report['missing_data_summary'].items():
                    self.log(f"    • {field}: {stats['missing_count']} records missing ({stats['percentage']})")
            
            if quality_report['recommendations']:
                self.log(f"\n  💡 Recommendations:")
                for rec in quality_report['recommendations'][:3]:  # Show first 3
                    self.log(f"    • {rec}")
            
            # Report errors
            if locked_pdfs:
                self.log(f"\n🔒 LOCKED PDFs ({len(locked_pdfs)}):")
                for pdf in locked_pdfs:
                    self.log(f"  - {pdf}")
            
            if other_errors:
                self.log(f"\n⚠️ OTHER ERRORS ({len(other_errors)}):")
                for pdf, error in other_errors:
                    self.log(f"  - {pdf}: {error}")
            
            self.log(f"\n📁 Files saved to: {self.selected_folder}")
            self.log(f"📝 Error log saved to: logs/wob_extractor_{datetime.now().strftime('%Y%m%d')}.log")
            if quality_file:
                self.log(f"📈 Quality report saved to: {os.path.basename(quality_file)}")
            
            # Show completion message
            total_subjects = sum(len(r.get('records', [])) for r in results if 'error' not in r)
            total_social_media = sum(platform_stats.values()) if platform_stats else 0
            
            success_msg = f"Data extraction complete!\n\n" + \
                         f"Processed: {len(pdf_files)} files\n" + \
                         f"Successful: {len(pdf_files) - len(locked_pdfs) - len(other_errors)} files\n" + \
                         f"Found: {total_subjects} subjects\n" + \
                         f"Social Media Accounts: {total_social_media}\n"
            
            # Add platform breakdown to success message
            if platform_stats and total_social_media > 0:
                success_msg += "\nTop Platforms:\n"
                for platform, count in sorted(platform_stats.items(), key=lambda x: x[1], reverse=True)[:3]:
                    percentage = (count / total_social_media) * 100
                    success_msg += f"  • {platform}: {count} ({percentage:.1f}%)\n"
            
            # Add extraction quality summary
            if quality_report['field_success_rates']:
                avg_success_rate = sum(float(stats['success_rate'].rstrip('%')) 
                                      for stats in quality_report['field_success_rates'].values()) / len(quality_report['field_success_rates'])
                success_msg += f"\nAverage field extraction rate: {avg_success_rate:.1f}%\n"
            
            if locked_pdfs:
                success_msg += f"\n⚠️ {len(locked_pdfs)} locked PDFs could not be processed"
            if other_errors:
                success_msg += f"\n⚠️ {len(other_errors)} files had errors"
            
            if quality_report['extraction_warnings']:
                success_msg += f"\n⚠️ {len(quality_report['extraction_warnings'])} records have missing fields"
            
            success_msg += "\n\nGenerated Files:\n"
            success_msg += "• Social Media Data CSV (with User IDs)\n"
            success_msg += "• Concerns Data CSV (with Other field)\n"
            success_msg += "• Analytics Summary Report\n"
            success_msg += "• Extraction Quality Report\n"
            success_msg += "• Detailed logs"
            
            messagebox.showinfo("Processing Complete", success_msg)
            
        except Exception as e:
            self.log(f"\n❌ Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred:\n\n{str(e)}")
        finally:
            self.process_btn.config(state="normal")

def main():
    root = tk.Tk()
    app = WOBExtractorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
