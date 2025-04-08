from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pandas as pd
import os
import re
import logging

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_days(text, pattern):
    """Extract days from text using regex pattern"""
    if pd.isna(text) or not isinstance(text, str):
        return None
    
    match = re.search(pattern, str(text))
    return float(match.group(1)) if match else None

def find_header_row(df, required_columns):
    """Find the first row containing all required columns"""
    for i in range(min(20, len(df))):  # Check first 20 rows
        row_values = [str(cell).strip().lower() for cell in df.iloc[i]]
        if all(any(col.lower() in val for val in row_values) for col in required_columns):
            return i
    return None

def process_sheet(file_path, sheet_name, required_columns):
    """Process a single sheet from Excel file"""
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        header_row = find_header_row(df, required_columns)
        
        if header_row is None:
            logger.warning(f"No header row found in sheet {sheet_name}")
            return None
            
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
        df.columns = [str(col).strip() for col in df.columns]
        
        # Verify required columns exist
        if not all(any(col in str(df_column).lower() for df_column in df.columns for col in required_columns)):
            logger.warning(f"Required columns not found in sheet {sheet_name}")
            return None
            
        return df
    except Exception as e:
        logger.error(f"Error processing sheet {sheet_name}: {str(e)}")
        return None

def process_files(pointage_path, paie_path):
    """Main processing function"""
    try:
        # Process pointage file
        pointage_data = {}
        pointage_required = ['nom et prenom', 'heures travaillees']
        
        with pd.ExcelFile(pointage_path) as xls:
            for sheet_name in xls.sheet_names:
                df = process_sheet(pointage_path, sheet_name, pointage_required)
                if df is not None:
                    nom_col = next(col for col in df.columns if 'nom' in str(col).lower())
                    heures_col = next(col for col in df.columns if 'heure' in str(col).lower())
                    
                    for _, row in df.iterrows():
                        name = str(row[nom_col]).strip().upper()
                        days = extract_days(row[heures_col], r'(\d+)\s*j\s*trav')
                        if name and days is not None:
                            pointage_data[name] = days
                    break

        # Process paie file
        paie_data = {}
        paie_required = ['nom et prenom', 'jrs/hrs']
        
        with pd.ExcelFile(paie_path) as xls:
            for sheet_name in xls.sheet_names:
                df = process_sheet(paie_path, sheet_name, paie_required)
                if df is not None:
                    nom_col = next(col for col in df.columns if 'nom' in str(col).lower())
                    jours_col = next(col for col in df.columns if 'jrs' in str(col).lower())
                    
                    for _, row in df.iterrows():
                        name = str(row[nom_col]).strip().upper()
                        days = extract_days(row[jours_col], r'(\d+\.?\d*)')
                        if name and days is not None:
                            paie_data[name] = days
                    break

        # Compare data
        results = []
        all_names = set(pointage_data.keys()).union(set(paie_data.keys()))
        
        for name in sorted(all_names):
            days_worked = pointage_data.get(name)
            days_paid = paie_data.get(name)
            
            if days_worked is None:
                status = "Employé absent dans pointage"
            elif days_paid is None:
                status = "Employé absent dans journal de paie"
            else:
                difference = days_paid - days_worked
                status = "Correct" if difference == 0 else "Incohérence"
                
            results.append({
                "name": name,
                "days_worked": days_worked,
                "days_paid": days_paid,
                "difference": days_paid - days_worked if None not in (days_worked, days_paid) else None,
                "status": status
            })

        # Generate summary
        status_counts = {"Correct": 0, "Incohérence": 0, 
                        "Employé absent dans pointage": 0, 
                        "Employé absent dans journal de paie": 0}
        
        for item in results:
            status_counts[item["status"]] += 1

        return {
            "results": results,
            "summary": {
                "total": len(results),
                "correct": status_counts["Correct"],
                "inconsistencies": status_counts["Incohérence"],
                "missing_in_pointage": status_counts["Employé absent dans pointage"],
                "missing_in_paie": status_counts["Employé absent dans journal de paie"]
            }
        }

    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return {"error": str(e)}

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'pointage' not in request.files or 'paie' not in request.files:
        return jsonify({"error": "Both files are required"}), 400
        
    pointage_file = request.files['pointage']
    paie_file = request.files['paie']
    
    if not (allowed_file(pointage_file.filename) and allowed_file(paie_file.filename)):
        return jsonify({"error": "Only Excel files (.xlsx, .xls) are allowed"}), 400

    try:
        # Save files temporarily
        pointage_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(pointage_file.filename))
        paie_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(paie_file.filename))
        
        pointage_file.save(pointage_path)
        paie_file.save(paie_path)
        
        # Process files
        result = process_files(pointage_path, paie_path)
        
        # Clean up
        os.remove(pointage_path)
        os.remove(paie_path)
        
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002, debug=True)