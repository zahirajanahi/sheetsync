import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import fitz  # PyMuPDF
import re
import os
import pytesseract
from PIL import Image
import io
import pandas as pd

class ExcelRIBComparator:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel RIB Comparator")
        self.root.geometry("1000x750")
        
        # Set up Tesseract path - MODIFY THIS PATH TO MATCH YOUR TESSERACT INSTALLATION
        # For Windows users this might be: r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        # For Mac users with Homebrew: '/usr/local/bin/tesseract'
        # For Linux users: '/usr/bin/tesseract'
        tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Default Windows path
        if os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Configure styles
        style = ttk.Style()
        style.configure('TFrame', background='#f5f5f5')
        style.configure('TLabel', background='#f5f5f5')
        self.root.configure(bg="#f5f5f5")
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="File Selection")
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Excel file
        ttk.Label(file_frame, text="Employee Excel File:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.excel_entry = ttk.Entry(file_frame, width=50)
        self.excel_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(file_frame, text="Browse", command=lambda: self.browse_file(self.excel_entry, [("Excel files", "*.xlsx *.xls")]),
                  bg="#4287f5", fg="white", relief=tk.RAISED).grid(row=0, column=2, padx=5, pady=5)
        
        # RIB file
        ttk.Label(file_frame, text="RIB PDF File:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.rib_entry = ttk.Entry(file_frame, width=50)
        self.rib_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Button(file_frame, text="Browse", command=lambda: self.browse_file(self.rib_entry, [("PDF files", "*.pdf")]),
                  bg="#4287f5", fg="white", relief=tk.RAISED).grid(row=1, column=2, padx=5, pady=5)
        
        # OCR settings
        ocr_frame = ttk.LabelFrame(main_frame, text="OCR Settings")
        ocr_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.use_ocr = tk.BooleanVar(value=True)
        ttk.Checkbutton(ocr_frame, text="Use OCR for scanned PDFs", variable=self.use_ocr).pack(side=tk.LEFT, padx=10)
        
        # Tesseract path setting
        ttk.Label(ocr_frame, text="Tesseract Path:").pack(side=tk.LEFT, padx=(20, 5))
        self.tesseract_path = ttk.Entry(ocr_frame, width=40)
        self.tesseract_path.pack(side=tk.LEFT, padx=5)
        self.tesseract_path.insert(0, pytesseract.pytesseract.tesseract_cmd)
        
        tk.Button(ocr_frame, text="Set", command=self.set_tesseract_path,
                 bg="#4287f5", fg="white", relief=tk.RAISED).pack(side=tk.LEFT, padx=5)
        
        # Employee selection frame
        employee_frame = ttk.LabelFrame(main_frame, text="Employee Selection")
        employee_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(employee_frame, text="Select Employee:").pack(side=tk.LEFT, padx=5, pady=5)
        self.employee_combo = ttk.Combobox(employee_frame, width=40, state="readonly")
        self.employee_combo.pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(employee_frame, text="Load Employees", command=self.load_employees,
                 bg="#4287f5", fg="white", relief=tk.RAISED).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Comparison Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a frame for employee details
        details_frame = ttk.Frame(results_frame)
        details_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Employee details
        ttk.Label(details_frame, text="Employee Name:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(details_frame, textvariable=self.name_var, width=40, state="readonly").grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(details_frame, text="Excel Account Number:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.excel_account_var = tk.StringVar()
        ttk.Entry(details_frame, textvariable=self.excel_account_var, width=40, state="readonly").grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(details_frame, text="RIB Account Number:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.rib_account_var = tk.StringVar()
        ttk.Entry(details_frame, textvariable=self.rib_account_var, width=40, state="readonly").grid(row=2, column=1, padx=5, pady=5)
        
        # Match result
        self.match_label = ttk.Label(details_frame, text="", font=("Arial", 12, "bold"))
        self.match_label.grid(row=3, column=0, columnspan=2, padx=5, pady=10)
        
        # Text display for extracted content
        text_frame = ttk.Frame(results_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.text_display = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, width=100, height=20)
        self.text_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Compare button
        compare_button = tk.Button(main_frame, text="COMPARE ACCOUNT NUMBERS", command=self.compare_account_numbers,
                                 bg="#4287f5", fg="white", relief=tk.RAISED, font=("Arial", 10, "bold"))
        compare_button.pack(pady=10)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(fill=tk.X)
        
        # Store employee data
        self.employees_df = None
    
    def browse_file(self, entry_widget, filetypes):
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filename)
    
    def set_tesseract_path(self):
        """Set the Tesseract OCR executable path"""
        path = self.tesseract_path.get()
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            messagebox.showinfo("Success", "Tesseract path set successfully!")
        else:
            messagebox.showerror("Error", f"Invalid path: {path}\nPlease provide the correct path to tesseract.exe")
    
    def load_employees(self):
        """Load employees from Excel file into the dropdown"""
        excel_path = self.excel_entry.get()
        
        if not excel_path:
            messagebox.showwarning("Warning", "Please select an Excel file")
            return
        
        try:
            self.status_var.set("Loading employee data...")
            self.root.update()
            
            # Read the Excel file
            self.employees_df = pd.read_excel(excel_path)
            
            # Check if required columns exist
            required_columns = ["Nom", "Prenom", "NO COMPTE"]
            missing_columns = [col for col in required_columns if col not in self.employees_df.columns]
            
            if missing_columns:
                messagebox.showerror("Error", f"Missing required columns: {', '.join(missing_columns)}\n"
                                    "Excel file must contain columns: Nom, Prenom, NO COMPTE")
                return
            
            # Prepare employee list for dropdown
            employee_list = []
            for _, row in self.employees_df.iterrows():
                employee_name = f"{row['Nom']} {row['Prenom']}"
                employee_list.append(employee_name)
            
            # Update combobox
            self.employee_combo['values'] = employee_list
            if employee_list:
                self.employee_combo.current(0)
            
            self.status_var.set(f"Loaded {len(employee_list)} employees")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read Excel file: {str(e)}")
            self.status_var.set("Error loading employee data")
    
    def extract_text_from_image(self, image):
        """Extract text from an image using OCR"""
        try:
            return pytesseract.image_to_string(image)
        except Exception as e:
            messagebox.showerror("OCR Error", f"Error during OCR: {str(e)}\n\nMake sure Tesseract is installed and the path is correct.")
            return ""
        
    def extract_text_from_pdf(self, pdf_path):
        """Extract all text from a PDF file with OCR for scanned documents"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            # First try normal text extraction
            for page in doc:
                page_text = page.get_text()
                text += page_text
            
            # If OCR is enabled and very little text was extracted, it's likely a scanned PDF
            if self.use_ocr.get() and len(text.strip()) < 50:  # Arbitrary threshold
                self.status_var.set("PDF appears to be scanned. Using OCR...")
                self.root.update()
                
                text = ""  # Reset text
                # Process each page with OCR
                for page_num, page in enumerate(doc):
                    # Get the page as a PNG image
                    pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))  # 2x zoom for better OCR
                    img_data = pix.tobytes("png")
                    
                    # Convert to PIL Image
                    img = Image.open(io.BytesIO(img_data))
                    
                    # Use Tesseract OCR
                    page_text = self.extract_text_from_image(img)
                    text += page_text + "\n"
                    
                    # Update status
                    self.status_var.set(f"OCR processing page {page_num+1}/{len(doc)}...")
                    self.root.update()
            
            return text
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read PDF: {str(e)}")
            return None
    
    def extract_account_number(self, text):
        """Extract account number from text using multiple methods for robustness"""
        # Strategy 1: Look for standard RIB pattern (20-24 consecutive digits)
        rib_pattern = r'\b\d{20,24}\b'
        matches = re.findall(rib_pattern, text)
        
        # Strategy 2: Remove spaces and look again (handles "FR76 1234 5678 9012...")
        clean_text = re.sub(r'\s', '', text)
        clean_matches = re.findall(rib_pattern, clean_text)
        
        # Strategy 3: Look for IBAN pattern with FR prefix
        iban_pattern = r'FR\s*\d{2}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{3}'
        iban_matches = re.findall(iban_pattern, text, re.IGNORECASE)
        
        # Strategy 4: Look for groups of 4-5 digits that could form a RIB
        groups_pattern = r'\d{4,5}\s+\d{4,5}\s+\d{4,5}\s+\d{4,5}\s+\d{4,5}'
        groups_matches = re.findall(groups_pattern, text)
        
        # Strategy 5: Look for any sequence of digits and spaces that has 20+ digits when spaces are removed
        potential_ribs = []
        digit_sequences = re.findall(r'[\d\s]{25,40}', text)
        for seq in digit_sequences:
            digits_only = re.sub(r'\s', '', seq)
            if len(digits_only) >= 20 and len(digits_only) <= 27:  # Allow some margin
                potential_ribs.append(digits_only)
        
        # Combine all strategies
        all_matches = matches[:]
        
        # Add clean matches if they're not already in the list
        all_matches.extend([m for m in clean_matches if m not in all_matches])
        
        # Process IBAN matches - extract just the digits
        for iban in iban_matches:
            iban_digits = re.sub(r'\D', '', iban)
            if iban_digits not in all_matches:
                all_matches.append(iban_digits)
        
        # Process group matches - join and remove spaces
        for group in groups_matches:
            group_digits = re.sub(r'\s', '', group)
            if group_digits not in all_matches:
                all_matches.append(group_digits)
        
        # Add potential RIBs
        all_matches.extend([p for p in potential_ribs if p not in all_matches])
        
        # Try to filter to most likely candidates (23-24 digits is standard for French RIB)
        rib_candidates = [m for m in all_matches if len(m) in [23, 24, 25, 27]]
        
        # If no candidates match the exact length, use the closest match
        if not rib_candidates and all_matches:
            # Sort by how close the length is to 24 digits
            all_matches.sort(key=lambda x: abs(len(x) - 24))
            rib_candidates = [all_matches[0]]
        
        if rib_candidates:
            return rib_candidates[0]  # Return the first match
        
        # Last resort: If we find any string of 20+ digits, return it
        if all_matches:
            all_matches.sort(key=len, reverse=True)  # Sort by length, longest first
            return all_matches[0]
        
        return None
    
    def find_employee_in_text(self, text, nom, prenom):
        """Check if the employee name appears in the PDF text"""
        # Try different name formats
        name_formats = [
            f"{nom} {prenom}",
            f"{prenom} {nom}",
            f"{nom.upper()} {prenom}",
            f"{nom} {prenom.upper()}",
            f"{nom.upper()} {prenom.upper()}",
            f"{prenom} {nom.upper()}",
            f"{prenom.upper()} {nom}"
        ]
        
        # Check each format
        for name_format in name_formats:
            if name_format.lower() in text.lower():
                return True
        
        return False
    
    def compare_account_numbers(self):
        """Compare account numbers between Excel and RIB PDF"""
        excel_path = self.excel_entry.get()
        rib_path = self.rib_entry.get()
        
        if not excel_path or not rib_path:
            messagebox.showwarning("Warning", "Please select both Excel and PDF files")
            return
        
        if self.employees_df is None:
            messagebox.showwarning("Warning", "Please load employee data first")
            return
        
        # Get selected employee
        selected_employee = self.employee_combo.get()
        if not selected_employee:
            messagebox.showwarning("Warning", "Please select an employee")
            return
        
        # Split name into first and last name
        nom_prenom = selected_employee.split(' ', 1)
        if len(nom_prenom) != 2:
            messagebox.showwarning("Warning", "Invalid employee name format")
            return
        
        nom, prenom = nom_prenom
        
        # Get employee record from dataframe
        employee_record = self.employees_df[(self.employees_df['Nom'] == nom) & 
                                          (self.employees_df['Prenom'] == prenom)]
        
        if employee_record.empty:
            messagebox.showwarning("Warning", f"Could not find employee: {nom} {prenom}")
            return
        
        # Get account number from Excel
        excel_account = str(employee_record['NO COMPTE'].iloc[0])
        # Remove spaces and non-digit characters
        excel_account = re.sub(r'\D', '', excel_account)
        
        self.status_var.set("Extracting text from RIB PDF...")
        self.root.update()
        
        # Extract text from RIB PDF
        rib_text = self.extract_text_from_pdf(rib_path)
        
        if rib_text is None:
            self.status_var.set("Error reading PDF")
            return
        
        # Check if employee name is in the RIB document
        employee_found = self.find_employee_in_text(rib_text, nom, prenom)
        
        # Extract account number from RIB
        rib_account = self.extract_account_number(rib_text)
        
        # Update UI with results
        self.name_var.set(f"{nom} {prenom}")
        self.excel_account_var.set(excel_account or "Not found")
        self.rib_account_var.set(rib_account or "Not found")
        
        # Display extracted text
        self.text_display.config(state=tk.NORMAL)
        self.text_display.delete(1.0, tk.END)
        
        if employee_found:
            self.text_display.insert(tk.END, f"✓ Employee name '{nom} {prenom}' found in RIB document\n\n")
        else:
            self.text_display.insert(tk.END, f"⚠ Warning: Employee name '{nom} {prenom}' NOT found in RIB document\n\n")
        
        self.text_display.insert(tk.END, f"--- RIB Document Text (first 1000 chars) ---\n{rib_text[:1000]}...\n")
        self.text_display.config(state=tk.DISABLED)
        
        # Compare the account numbers
        if excel_account and rib_account:
            # Remove any non-digit characters for comparison
            clean_excel = re.sub(r'\D', '', excel_account)
            clean_rib = re.sub(r'\D', '', rib_account)
            
            # Check if one is a subset of the other (to handle partial account numbers)
            if clean_excel in clean_rib or clean_rib in clean_excel:
                self.match_label.config(text="✓ ACCOUNT NUMBERS MATCH", foreground="green")
            else:
                self.match_label.config(text="✗ ACCOUNT NUMBERS DO NOT MATCH", foreground="red")
        else:
            self.match_label.config(text="⚠ Could not find account numbers in one or both files", foreground="orange")
        
        self.status_var.set("Account number comparison complete")

if __name__ == "__main__":
    root = tk.Tk()
    app = ExcelRIBComparator(root)
    root.mainloop()