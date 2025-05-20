from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "Backend is working"}), 200

@app.route('/upload', methods=['POST'])
def upload_files():
    # Debug: Print all received files
    print("Files received:", list(request.files.keys()))
    
    # More flexible file name checking
    file_keys = list(request.files.keys())
    
    if len(file_keys) < 2:
        return jsonify({'error': 'Les deux fichiers sont requis', 'received': file_keys}), 400
    
    # Use the first two files regardless of their names
    file1 = request.files[file_keys[0]]
    file2 = request.files[file_keys[1]]

    if file1.filename == '' or file2.filename == '':
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400

    file1_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file1.filename))
    file2_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file2.filename))

    file1.save(file1_path)
    file2.save(file2_path)

    try:
        comparison_results = compare_files(file1_path, file2_path)
        return jsonify(comparison_results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def find_header_row(file_path, search_terms):
    """Find the row number that contains all search terms in an Excel file."""
    if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        df = pd.read_excel(file_path, header=None)
    elif file_path.endswith('.csv'):
        df = pd.read_csv(file_path, delimiter=";", encoding="ISO-8859-1", header=None, low_memory=False)
    else:
        raise ValueError("Format de fichier non supporté")
    
    # Convert all cells to strings and uppercase for case-insensitive search
    df = df.applymap(lambda x: str(x).upper().strip() if pd.notna(x) else "")
    
    for idx, row in df.iterrows():
        row_values = ' '.join(row.values.astype(str))
        if all(term.upper() in row_values for term in search_terms):
            return idx
    return None

def read_file_with_header(file_path, header_terms):
    """Read file with dynamic header row detection."""
    header_row = find_header_row(file_path, header_terms)
    if header_row is None:
        raise ValueError(f"Could not find header row containing: {header_terms}")
    
    if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        df = pd.read_excel(file_path, header=header_row)
    elif file_path.endswith('.csv'):
        df = pd.read_csv(file_path, delimiter=";", encoding="ISO-8859-1", header=header_row, low_memory=False)
    else:
        raise ValueError("Format de fichier non supporté")
    
    # Clean column names
    df.columns = [str(col).strip().upper() for col in df.columns]
    return df

def compare_files(file1_path, file2_path):
    # Read files with dynamic header detection
    try:
        # Assuming both files have NCIN and we need to compare column_1 from file1 with column_2 from file2
        df_file1 = read_file_with_header(file1_path, ["NCIN", "COLUMN_1"])
        df_file2 = read_file_with_header(file2_path, ["NCIN", "COLUMN_2"])
    except ValueError as e:
        raise Exception(f"Erreur lors de la lecture des fichiers: {str(e)}")
    
    # Print column names for debugging
    print("File1 columns:", df_file1.columns.tolist())
    print("File2 columns:", df_file2.columns.tolist())
    
    # Identify the correct columns - using more flexible matching
    ncin_col_file1 = next((col for col in df_file1.columns if "NCIN" in col or "CIN" in col), None)
    column1_file1 = next((col for col in df_file1.columns if "COLUMN_1" in col), None)
    
    ncin_col_file2 = next((col for col in df_file2.columns if "NCIN" in col or "CIN" in col), None)
    column2_file2 = next((col for col in df_file2.columns if "COLUMN_2" in col), None)
    
    # Check required columns
    required_file1_cols = {
        "NCIN": ncin_col_file1,
        "COLUMN_1": column1_file1
    }
    required_file2_cols = {
        "NCIN": ncin_col_file2,
        "COLUMN_2": column2_file2
    }
    missing_file1 = [k for k, v in required_file1_cols.items() if not v]
    missing_file2 = [k for k, v in required_file2_cols.items() if not v]
    if missing_file1:
        raise Exception(f"Colonnes manquantes dans File1: {', '.join(missing_file1)}. Colonnes disponibles: {df_file1.columns.tolist()}")
    if missing_file2:
        raise Exception(f"Colonnes manquantes dans File2: {', '.join(missing_file2)}. Colonnes disponibles: {df_file2.columns.tolist()}")
        
    # Clean and standardize NCIN for better matching
    df_file1[ncin_col_file1] = df_file1[ncin_col_file1].astype(str).str.strip().str.upper()
    df_file2[ncin_col_file2] = df_file2[ncin_col_file2].astype(str).str.strip().str.upper()
    
    # Filter out rows with empty/NaN NCIN values
    df_file1 = df_file1[df_file1[ncin_col_file1].str.strip() != '']
    df_file1 = df_file1[df_file1[ncin_col_file1] != 'NAN']
    df_file1 = df_file1[df_file1[ncin_col_file1] != 'N/A']
    
    df_file2 = df_file2[df_file2[ncin_col_file2].str.strip() != '']
    df_file2 = df_file2[df_file2[ncin_col_file2] != 'NAN']
    df_file2 = df_file2[df_file2[ncin_col_file2] != 'N/A']
    
    # Convert columns to numeric
    df_file1[column1_file1] = pd.to_numeric(df_file1[column1_file1], errors="coerce").fillna(0)
    df_file2[column2_file2] = pd.to_numeric(df_file2[column2_file2], errors="coerce").fillna(0)
    
    # Prepare dataframes for merge
    df_file1_prepared = df_file1[[ncin_col_file1, column1_file1]].rename(
        columns={ncin_col_file1: "CIN", column1_file1: "COLUMN_1_VALUE"}
    )
    
    df_file2_prepared = df_file2[[ncin_col_file2, column2_file2]].rename(
        columns={ncin_col_file2: "CIN", column2_file2: "COLUMN_2_VALUE"}
    )
    
    # Merge on CIN - using outer join to catch all cases
    df_comparison = pd.merge(df_file1_prepared, df_file2_prepared, on="CIN", how="outer").fillna(0)
    df_comparison["DIFFERENCE"] = df_comparison["COLUMN_1_VALUE"] - df_comparison["COLUMN_2_VALUE"]
    
    # Generate results
    results = []
    for _, row in df_comparison.iterrows():
        # Skip rows with empty/NaN CIN values in the final results
        if pd.isna(row["CIN"]) or str(row["CIN"]).strip() in ['', 'NAN', 'N/A']:
            continue
            
        status = "Correct"  # Default to correct unless we find issues
        inconsistencies = []
        
        # Check for record existence in both files
        in_file1 = any(df_file1[ncin_col_file1] == row["CIN"])
        in_file2 = any(df_file2[ncin_col_file2] == row["CIN"])
        
        if not in_file1 and in_file2:
            status = "NCIN absent dans fichier 1"
            inconsistencies.append("NCIN absent dans fichier 1")
        elif in_file1 and not in_file2:
            status = "NCIN absent dans fichier 2"
            inconsistencies.append("NCIN absent dans fichier 2")
        else:
            # Values comparison
            if abs(row["DIFFERENCE"]) > 0.01:
                status = "Incohérence"
                inconsistencies.append(f"Valeur fichier 1: {row['COLUMN_1_VALUE']:.2f} Valeur fichier 2: {row['COLUMN_2_VALUE']:.2f} Différence de {abs(row['DIFFERENCE']):.2f}")
        
        result_item = {
            "CIN": row["CIN"],
            "column1Value": row["COLUMN_1_VALUE"],
            "column2Value": row["COLUMN_2_VALUE"],
            "difference": row["DIFFERENCE"],
            "status": status,
            "inconsistencies": inconsistencies
        }
        
        results.append(result_item)
    
    return {
        "results": results,
        "summary": {
            "total": len(results),
            "correct": sum(1 for r in results if r["status"] == "Correct"),
            "inconsistencies": sum(1 for r in results if r["status"] != "Correct"),
            "missingInFile1": sum(1 for r in results if r["status"] == "NCIN absent dans fichier 1"),
            "missingInFile2": sum(1 for r in results if r["status"] == "NCIN absent dans fichier 2"),
            "valueDifferences": sum(1 for r in results if "Incohérence" == r["status"])
        }
    }

if __name__ == '__main__':
    app.run(debug=True, port=8007)