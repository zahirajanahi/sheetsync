import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import fitz  # PyMuPDF
import re
import os
import pytesseract
from PIL import Image
import io
import tempfile

class RIBPDFComparator:
    def __init__(self, root):
        self.root = root
        self.root.title("RIB PDF Comparator")
        self.root.geometry("900x700")
        
        # Set up Tesseract path - MODIFY THIS PATH TO MATCH YOUR TESSERACT INSTALLATION
        # For Windows users this might be: r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        # For Mac users with Homebrew: '/usr/local/bin/tesseract'
        # For Linux users: '/usr/bin/tesseract'
        tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Default Windows path
        if os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Configure styles
        self.root.configure(bg="#f5f5f5")
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for different comparison modes
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create RIB comparison tab
        self.create_rib_tab()
        
        # Create full PDF comparison tab (your original code)
        self.create_full_comparison_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(fill=tk.X)
    
    def create_rib_tab(self):
        """Create the specialized RIB comparison tab"""
        rib_frame = ttk.Frame(self.notebook)
        self.notebook.add(rib_frame, text="RIB Check")
        
        # File selection frame
        file_frame = ttk.Frame(rib_frame)
        file_frame.pack(fill=tk.X, pady=10)
        
        # Fiche Personnelle
        ttk.Label(file_frame, text="Fiche Personnelle PDF:").grid(row=0, column=0, sticky="e")
        self.fiche_entry = ttk.Entry(file_frame, width=50)
        self.fiche_entry.grid(row=0, column=1, padx=5)
        
        tk.Button(file_frame, text="Browse", command=lambda: self.browse_file(self.fiche_entry),
                  bg="#4287f5", fg="white", relief=tk.RAISED).grid(row=0, column=2)
        
        # RIB file
        ttk.Label(file_frame, text="RIB PDF:").grid(row=1, column=0, sticky="e")
        self.rib_entry = ttk.Entry(file_frame, width=50)
        self.rib_entry.grid(row=1, column=1, padx=5)
        
        tk.Button(file_frame, text="Browse", command=lambda: self.browse_file(self.rib_entry),
                  bg="#4287f5", fg="white", relief=tk.RAISED).grid(row=1, column=2)
        
        # OCR settings
        ocr_frame = ttk.LabelFrame(rib_frame, text="OCR Settings")
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
        
        # Results frame
        results_frame = ttk.Frame(rib_frame)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # RIB numbers frame
        rib_display_frame = ttk.LabelFrame(results_frame, text="RIB Numbers")
        rib_display_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # RIB from first file
        ttk.Label(rib_display_frame, text="Fiche Personnelle RIB:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.fiche_rib_var = tk.StringVar()
        ttk.Entry(rib_display_frame, textvariable=self.fiche_rib_var, width=40, state="readonly").grid(row=0, column=1, padx=5, pady=5)
        
        # RIB from second file
        ttk.Label(rib_display_frame, text="RIB Document:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.doc_rib_var = tk.StringVar()
        ttk.Entry(rib_display_frame, textvariable=self.doc_rib_var, width=40, state="readonly").grid(row=1, column=1, padx=5, pady=5)
        
        # Comparison result
        self.match_label = ttk.Label(rib_display_frame, text="", font=("Arial", 12, "bold"))
        self.match_label.grid(row=2, column=0, columnspan=2, padx=5, pady=10)
        
        # Text display for extracted content
        text_frame = ttk.LabelFrame(results_frame, text="Extracted Text")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.text_display = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, width=100, height=15)
        self.text_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Compare button
        compare_button = tk.Button(rib_frame, text="COMPARE RIB NUMBERS", command=self.compare_rib_numbers,
                                 bg="#4287f5", fg="white", relief=tk.RAISED, font=("Arial", 10, "bold"))
        compare_button.pack(pady=10)
    
    def set_tesseract_path(self):
        """Set the Tesseract OCR executable path"""
        path = self.tesseract_path.get()
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            messagebox.showinfo("Success", "Tesseract path set successfully!")
        else:
            messagebox.showerror("Error", f"Invalid path: {path}\nPlease provide the correct path to tesseract.exe")
            
    def extract_text_from_image(self, image):
        """Extract text from an image using OCR"""
        try:
            return pytesseract.image_to_string(image)
        except Exception as e:
            messagebox.showerror("OCR Error", f"Error during OCR: {str(e)}\n\nMake sure Tesseract is installed and the path is correct.")
            return ""
        
    def create_full_comparison_tab(self):
        """Create the full PDF comparison tab (your original code)"""
        full_frame = ttk.Frame(self.notebook)
        self.notebook.add(full_frame, text="Full PDF Comparison")
        
        # File selection frame
        file_frame = ttk.Frame(full_frame)
        file_frame.pack(fill=tk.X, pady=10)
        
        # File 1
        ttk.Label(file_frame, text="First PDF:").grid(row=0, column=0, sticky="e")
        self.file1_entry = ttk.Entry(file_frame, width=50)
        self.file1_entry.grid(row=0, column=1, padx=5)
        
        tk.Button(file_frame, text="Browse", command=lambda: self.browse_file(self.file1_entry),
                  bg="#4287f5", fg="white", relief=tk.RAISED).grid(row=0, column=2)
        
        # File 2
        ttk.Label(file_frame, text="Second PDF:").grid(row=1, column=0, sticky="e")
        self.file2_entry = ttk.Entry(file_frame, width=50)
        self.file2_entry.grid(row=1, column=1, padx=5)
        
        tk.Button(file_frame, text="Browse", command=lambda: self.browse_file(self.file2_entry),
                  bg="#4287f5", fg="white", relief=tk.RAISED).grid(row=1, column=2)
        
        # Options frame
        options_frame = ttk.Frame(full_frame)
        options_frame.pack(fill=tk.X, pady=10)
        
        self.ignore_case = tk.BooleanVar()
        self.ignore_punctuation = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Ignore Case", variable=self.ignore_case).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(options_frame, text="Ignore Punctuation", variable=self.ignore_punctuation).pack(side=tk.LEFT, padx=10)
        
        # Compare button
        compare_button = tk.Button(full_frame, text="COMPARE WORDS", command=self.compare_files,
                                 bg="#4287f5", fg="white", relief=tk.RAISED, font=("Arial", 10, "bold"))
        compare_button.pack(pady=10)
        
        # Results notebook for full comparison
        self.full_notebook = ttk.Notebook(full_frame)
        self.full_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Diff tab
        diff_frame = ttk.Frame(self.full_notebook)
        self.diff_text = scrolledtext.ScrolledText(diff_frame, wrap=tk.WORD, width=100, height=25, font=('Consolas', 10))
        self.diff_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.full_notebook.add(diff_frame, text="Word Differences")
        
        # Stats tab
        stats_frame = ttk.Frame(self.full_notebook)
        self.stats_text = scrolledtext.ScrolledText(stats_frame, wrap=tk.WORD, width=100, height=25)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.full_notebook.add(stats_frame, text="Statistics")
        
        # Configure tags for coloring
        self.diff_text.tag_config('diff', background="#ffdddd", foreground="red")
        self.diff_text.tag_config('match', foreground="#888888")
    
    def browse_file(self, entry_widget):
        filename = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if filename:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filename)
    
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
    
    def extract_rib_number(self, text):
        """Extract RIB number from text using multiple methods for robustness"""
        # Print debug information to help identify the issue
        print(f"Searching for RIB in text of length: {len(text)}")
        
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
        
        # Debug information
        print(f"Standard matches: {matches}")
        print(f"Clean matches: {clean_matches}")
        print(f"IBAN matches: {iban_matches}")
        print(f"Group matches: {groups_matches}")
        print(f"Potential RIBs: {potential_ribs}")
        
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
        
        # Print final candidates
        print(f"Final RIB candidates: {rib_candidates}")
        
        if rib_candidates:
            return rib_candidates[0]  # Return the first match
        
        # Last resort: If we find any string of 20+ digits, return it
        if all_matches:
            all_matches.sort(key=len, reverse=True)  # Sort by length, longest first
            return all_matches[0]
        
        return None
    
    def compare_rib_numbers(self):
        """Compare RIB numbers from both PDF files"""
        fiche_path = self.fiche_entry.get()
        rib_path = self.rib_entry.get()
        
        if not fiche_path or not rib_path:
            messagebox.showwarning("Warning", "Please select both PDF files")
            return
        
        self.status_var.set("Extracting RIB numbers...")
        self.root.update()
        
        # Extract text from both PDFs
        fiche_text = self.extract_text_from_pdf(fiche_path)
        rib_text = self.extract_text_from_pdf(rib_path)
        
        if fiche_text is None or rib_text is None:
            self.status_var.set("Error reading PDFs")
            return
        
        # Display extracted text
        self.text_display.config(state=tk.NORMAL)
        self.text_display.delete(1.0, tk.END)
        self.text_display.insert(tk.END, f"--- Fiche Personnelle Text ---\n{fiche_text[:500]}...\n\n")
        self.text_display.insert(tk.END, f"--- RIB Document Text ---\n{rib_text[:500]}...\n")
        self.text_display.config(state=tk.DISABLED)
        
        # Extract RIB numbers from both texts
        fiche_rib = self.extract_rib_number(fiche_text)
        rib_doc_number = self.extract_rib_number(rib_text)
        
        # Update the UI with extracted RIB numbers
        self.fiche_rib_var.set(fiche_rib or "Not found")
        self.doc_rib_var.set(rib_doc_number or "Not found")
        
        # Compare the RIB numbers
        if fiche_rib and rib_doc_number:
            if fiche_rib == rib_doc_number:
                self.match_label.config(text="✓ RIB NUMBERS MATCH", foreground="green")
            else:
                self.match_label.config(text="✗ RIB NUMBERS DO NOT MATCH", foreground="red")
        else:
            self.match_label.config(text="⚠ Could not find RIB numbers in one or both files", foreground="orange")
        
        self.status_var.set("RIB comparison complete")
    
    def clean_text(self, text):
        """Clean and normalize text based on settings (for full comparison)"""
        if self.ignore_case.get():
            text = text.lower()
        if self.ignore_punctuation.get():
            import string
            text = text.translate(str.maketrans('', '', string.punctuation))
        return text
    
    def extract_words(self, pdf_path):
        """Extract words from PDF with position information (for full comparison)"""
        try:
            doc = fitz.open(pdf_path)
            words = []
            for page in doc:
                word_blocks = page.get_text("words")
                for word in word_blocks:
                    words.append(word[4])  # The actual word text
            return words
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read PDF: {str(e)}")
            return None
    
    def compare_files(self):
        """Full PDF comparison (original functionality)"""
        file1 = self.file1_entry.get()
        file2 = self.file2_entry.get()
        
        if not file1 or not file2:
            messagebox.showwarning("Warning", "Please select both PDF files")
            return
        
        self.status_var.set("Extracting words...")
        self.root.update()
        
        words1 = self.extract_words(file1)
        words2 = self.extract_words(file2)
        
        if words1 is None or words2 is None:
            self.status_var.set("Ready")
            return
        
        # Clean words based on settings
        words1 = [self.clean_text(w) for w in words1 if w.strip()]
        words2 = [self.clean_text(w) for w in words2 if w.strip()]
        
        # Prepare the display
        self.diff_text.config(state=tk.NORMAL)
        self.diff_text.delete(1.0, tk.END)
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        
        # Find word differences
        from difflib import Differ
        differ = Differ()
        diff = list(differ.compare(words1, words2))
        
        # Process the diff
        diff_words = []
        file1_only = []
        file2_only = []
        
        for item in diff:
            code = item[0]
            word = item[2:].strip()
            
            if not word:
                continue
                
            if code == ' ':
                # Words match
                self.diff_text.insert(tk.END, word + ' ', 'match')
            elif code == '-':
                # Word only in file1
                diff_words.append(('file1', word))
                file1_only.append(word)
                self.diff_text.insert(tk.END, word + ' ', 'diff')
            elif code == '+':
                # Word only in file2
                diff_words.append(('file2', word))
                file2_only.append(word)
                self.diff_text.insert(tk.END, word + ' ', 'diff')
        
        # Generate statistics
        self.stats_text.insert(tk.END, f"Comparison Statistics\n{'='*30}\n\n")
        self.stats_text.insert(tk.END, f"Total words in File 1: {len(words1)}\n")
        self.stats_text.insert(tk.END, f"Total words in File 2: {len(words2)}\n")
        self.stats_text.insert(tk.END, f"\nUnique words in File 1 only: {len(file1_only)}\n")
        self.stats_text.insert(tk.END, f"Unique words in File 2 only: {len(file2_only)}\n")
        
        if file1_only:
            self.stats_text.insert(tk.END, "\nWords only in File 1:\n")
            self.stats_text.insert(tk.END, ', '.join(sorted(set(file1_only))))
        
        if file2_only:
            self.stats_text.insert(tk.END, "\n\nWords only in File 2:\n")
            self.stats_text.insert(tk.END, ', '.join(sorted(set(file2_only))))
        
        # Finalize
        self.diff_text.config(state=tk.DISABLED)
        self.stats_text.config(state=tk.DISABLED)
        self.status_var.set(f"Comparison complete - {len(diff_words)} differences found")

if __name__ == "__main__":
    root = tk.Tk()
    app = RIBPDFComparator(root)
    root.mainloop()