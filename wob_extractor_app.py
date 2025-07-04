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
        self.root.geometry("700x600")
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.extractor = SmartExtractor(self.config_manager)
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
            
            for i, pdf in enumerate(pdf_files):
                self.log(f"\n📖 Processing: {os.path.basename(pdf)}")
                result = self.extractor.extract_from_pdf(pdf)
                
                if 'error' in result:
                    self.log(f"  ⚠️ Warning: {result['error']}")
                else:
                    num_records = len(result.get('records', []))
                    self.log(f"  ✓ Found {num_records} subjects of concern")
                
                results.append(result)
                self.progress['value'] = i + 1
                self.root.update()
            
            # Generate output files
            self.log("\n📊 Generating output files...")
            account_count, soc_count, concerns_count = self.output_gen.generate_reports(
                results, self.selected_folder, month_year
            )
            
            self.log(f"\n✅ COMPLETE!")
            self.log(f"  - Account Tracker: {account_count} records")
            self.log(f"  - SOC List: {soc_count} records")
            self.log(f"  - Concerns Data: {concerns_count} records")
            self.log(f"\n📁 Files saved to: {self.selected_folder}")
            
            messagebox.showinfo("Success", 
                f"Data extraction complete!\n\n" +
                f"Processed: {len(pdf_files)} files\n" +
                f"Found: {sum(len(r.get('records', [])) for r in results if 'error' not in r)} subjects\n\n" +
                f"Check the folder for output CSV files.")
            
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