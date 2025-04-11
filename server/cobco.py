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
    if 'pointage' not in request.files or 'paie' not in request.files:
        return jsonify({'error': 'Les deux fichiers sont requis'}), 400

    pointage_file = request.files['pointage']
    paie_file = request.files['paie']

    if pointage_file.filename == '' or paie_file.filename == '':
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400

    pointage_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(pointage_file.filename))
    paie_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(paie_file.filename))

    pointage_file.save(pointage_path)
    paie_file.save(paie_path)

    try:
        comparison_results = compare_files(pointage_path, paie_path)
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

def compare_files(pointage_path, paie_path):
    # Read files with dynamic header detection
    try:
        # Both files now use NCIN and have JRS/HRS columns
        df_pointage = read_file_with_header(pointage_path, ["NCIN", "JRS/HRS"])
        df_paie = read_file_with_header(paie_path, ["NCIN", "JRS/HRS"])
    except ValueError as e:
        raise Exception(f"Erreur lors de la lecture des fichiers: {str(e)}")
    
    # Print column names for debugging
    print("Pointage columns:", df_pointage.columns.tolist())
    print("Paie columns:", df_paie.columns.tolist())
    
    # Identify the correct columns - using more flexible matching
    ncin_col_pointage = next((col for col in df_pointage.columns if "NCIN" in col or "CIN" in col), None)
    jrs_hrs_col_pointage = next((col for col in df_pointage.columns if "JRS" in col and "HRS" in col), None)
    
    # For the "HS 25" column in pointage
    hs25_pointage_col = next((col for col in df_pointage.columns if "HS 25" in col and "MT" not in col), None)
    
    # For the "jour férié" column in pointage
    ferie_pointage_col = None
    for col in df_pointage.columns:
        if "FERIE" in col or "FÉRIÉ" in col:
            ferie_pointage_col = col
            break
    
    # Also check for "JOUR FERIE" pattern separately to avoid duplication issues
    if not ferie_pointage_col:
        for col in df_pointage.columns:
            if "JOUR" in col and ("FERIE" in col or "FÉRIÉ" in col):
                ferie_pointage_col = col
                break
    
    # Paie file columns
    ncin_col_paie = next((col for col in df_paie.columns if "NCIN" in col or "CIN" in col), None)
    jrs_hrs_col_paie = next((col for col in df_paie.columns if "JRS" in col and "HRS" in col), None)
    
    # For the "HS 25" column in paie
    hs25_paie_col = next((col for col in df_paie.columns if "HS 25" in col and "MT" not in col), None)
    
    # For the "Férié" column in paie
    ferie_paie_col = None
    for col in df_paie.columns:
        if "FERIE" in col or "FÉRIÉ" in col:
            ferie_paie_col = col
            break
    
    # Check required columns
    required_pointage_cols = {
        "NCIN": ncin_col_pointage,
        "JRS/HRS": jrs_hrs_col_pointage
    }
    required_paie_cols = {
        "NCIN": ncin_col_paie,
        "JRS/HRS": jrs_hrs_col_paie
    }
    missing_pointage = [k for k, v in required_pointage_cols.items() if not v]
    missing_paie = [k for k, v in required_paie_cols.items() if not v]
    if missing_pointage:
        raise Exception(f"Colonnes manquantes dans Pointage: {', '.join(missing_pointage)}. Colonnes disponibles: {df_pointage.columns.tolist()}")
    if missing_paie:
        raise Exception(f"Colonnes manquantes dans Journal de Paie: {', '.join(missing_paie)}. Colonnes disponibles: {df_paie.columns.tolist()}")
        
    # Clean and standardize NCIN for better matching
    df_pointage[ncin_col_pointage] = df_pointage[ncin_col_pointage].astype(str).str.strip().str.upper()
    df_paie[ncin_col_paie] = df_paie[ncin_col_paie].astype(str).str.strip().str.upper()
    
    # Filter out rows with empty/NaN NCIN values
    df_paie = df_paie[df_paie[ncin_col_paie].str.strip() != '']
    df_paie = df_paie[df_paie[ncin_col_paie] != 'NAN']
    df_paie = df_paie[df_paie[ncin_col_paie] != 'N/A']
    
    # Convert columns to numeric
    df_pointage[jrs_hrs_col_pointage] = pd.to_numeric(df_pointage[jrs_hrs_col_pointage], errors="coerce").fillna(0)
    df_paie[jrs_hrs_col_paie] = pd.to_numeric(df_paie[jrs_hrs_col_paie], errors="coerce").fillna(0)
    
    # Convert ferié columns to numeric if they exist
    if ferie_pointage_col:
        df_pointage[ferie_pointage_col] = pd.to_numeric(df_pointage[ferie_pointage_col], errors="coerce").fillna(0)
    if ferie_paie_col:
        df_paie[ferie_paie_col] = pd.to_numeric(df_paie[ferie_paie_col], errors="coerce").fillna(0)
    
    # Convert HS 25 columns to numeric if they exist
    if hs25_pointage_col:
        df_pointage[hs25_pointage_col] = pd.to_numeric(df_pointage[hs25_pointage_col], errors="coerce").fillna(0)
    if hs25_paie_col:
        df_paie[hs25_paie_col] = pd.to_numeric(df_paie[hs25_paie_col], errors="coerce").fillna(0)
    
    # Group pointage by NCIN and aggregate data
    agg_dict = {
        jrs_hrs_col_pointage: 'sum'
    }
    
    if ferie_pointage_col:
        agg_dict[ferie_pointage_col] = 'sum'
    if hs25_pointage_col:
        agg_dict[hs25_pointage_col] = 'sum'
        
    df_pointage_grouped = df_pointage.groupby(ncin_col_pointage).agg(agg_dict).reset_index()
    
    # Rename columns for the grouped dataframe
    rename_dict_pointage = {
        ncin_col_pointage: "CIN",
        jrs_hrs_col_pointage: "Heures_Pointage"
    }
    
    if ferie_pointage_col:
        rename_dict_pointage[ferie_pointage_col] = "FERIE_POINTAGE"
    if hs25_pointage_col:
        rename_dict_pointage[hs25_pointage_col] = "HS25_POINTAGE"
        
    df_pointage_grouped.rename(columns=rename_dict_pointage, inplace=True)
    
    # Prepare paie data
    paie_cols = [ncin_col_paie, jrs_hrs_col_paie]
    if ferie_paie_col:
        paie_cols.append(ferie_paie_col)
    if hs25_paie_col:
        paie_cols.append(hs25_paie_col)
        
    rename_dict_paie = {
        ncin_col_paie: "CIN", 
        jrs_hrs_col_paie: "Heures_Paie"
    }
    
    if ferie_paie_col:
        rename_dict_paie[ferie_paie_col] = "FERIE_PAIE"
    if hs25_paie_col:
        rename_dict_paie[hs25_paie_col] = "HS25_PAIE"
        
    df_paie = df_paie[paie_cols].rename(columns=rename_dict_paie)
    
    # Merge on CIN - using outer join to catch all cases
    df_comparaison = pd.merge(df_paie, df_pointage_grouped, on="CIN", how="outer").fillna(0)
    df_comparaison["Écart"] = df_comparaison["Heures_Pointage"] - df_comparaison["Heures_Paie"]
    
    # Generate results
    results = []
    for _, row in df_comparaison.iterrows():
        # Skip rows with empty/NaN CIN values in the final results
        if pd.isna(row["CIN"]) or str(row["CIN"]).strip() in ['', 'NAN', 'N/A']:
            continue
            
        prime_rendement = 0
        status = "Correct"  # Default to correct unless we find issues
        inconsistencies = []
        
        # First check for employee absence cases
        # This is only for complete absence (CIN missing in one file)
        in_pointage = any(df_pointage[ncin_col_pointage] == row["CIN"])
        in_paie = any(df_paie["CIN"] == row["CIN"])
        
        if not in_pointage and in_paie:
            status = "Employé absent dans pointage"
            inconsistencies.append("Employé absent dans pointage")
        elif in_pointage and not in_paie:
            status = "Employé absent dans journal de paie"
            inconsistencies.append("Employé absent dans journal de paie")
        else:
            # Hours comparison (JRS/HRS vs JRS/HRS)
            # Check for hours discrepancy
            if abs(row["Écart"]) > 0.01:
                status = "Incohérence"
                inconsistencies.append(f"Heures Pointage: {row['Heures_Pointage']:.2f} Heures Paie: {row['Heures_Paie']:.2f} Différence de {abs(row['Écart']):.2f} heures")
                
                # Calculate Prime de Rendement when worked hours exceed paid hours
                if row["Heures_Pointage"] > row["Heures_Paie"]:
                    prime_rendement = row["Heures_Pointage"] - row["Heures_Paie"]
        
        # Férié comparison
        ferie_status = "Correct"
        if "FERIE_POINTAGE" in df_comparaison.columns and "FERIE_PAIE" in df_comparaison.columns:
            if abs(row["FERIE_POINTAGE"] - row["FERIE_PAIE"]) > 0.01:
                ferie_status = "Incohérence"
                if status == "Correct":
                    status = "Incohérence"
                inconsistencies.append(f"Férié Pointage ({row['FERIE_POINTAGE']}) ≠ Férié Paie ({row['FERIE_PAIE']})")
        elif "FERIE_POINTAGE" in df_comparaison.columns and row["FERIE_POINTAGE"] > 0:
            ferie_status = "Incohérence"
            if status == "Correct":
                status = "Incohérence"
            inconsistencies.append(f"Férié Pointage ({row['FERIE_POINTAGE']}) mais absent dans Paie")
        elif "FERIE_PAIE" in df_comparaison.columns and row["FERIE_PAIE"] > 0:
            ferie_status = "Incohérence"
            if status == "Correct":
                status = "Incohérence"
            inconsistencies.append(f"Férié Paie ({row['FERIE_PAIE']}) mais absent dans Pointage")
        
        # HS 25 comparison (HS 25 vs HS 25)
        hs25_status = "Correct"
        if "HS25_POINTAGE" in df_comparaison.columns and "HS25_PAIE" in df_comparaison.columns:
            if abs(row["HS25_POINTAGE"] - row["HS25_PAIE"]) > 0.01:
                hs25_status = "Incohérence"
                if status == "Correct":
                    status = "Incohérence"
                inconsistencies.append(f"HS 25 Pointage ({row['HS25_POINTAGE']}) ≠ HS 25 Paie ({row['HS25_PAIE']})")
        elif "HS25_POINTAGE" in df_comparaison.columns and row["HS25_POINTAGE"] > 0:
            hs25_status = "Incohérence"
            if status == "Correct":
                status = "Incohérence"
            inconsistencies.append(f"HS 25 Pointage ({row['HS25_POINTAGE']}) mais absent dans Paie")
        elif "HS25_PAIE" in df_comparaison.columns and row["HS25_PAIE"] > 0:
            hs25_status = "Incohérence"
            if status == "Correct":
                status = "Incohérence"
            inconsistencies.append(f"HS 25 Paie ({row['HS25_PAIE']}) mais absent dans Pointage")
        
        result_item = {
            "CIN": row["CIN"],
            "heuresTravaillees": row["Heures_Pointage"],
            "heuresPayees": row["Heures_Paie"],
            "difference": row["Écart"],
            "status": status,
            "primeRendement": prime_rendement,
            "ferieStatus": ferie_status,
            "hs25Status": hs25_status,
            "inconsistencies": inconsistencies
        }
        
        # Add optional fields if they exist in the dataframe
        if "FERIE_POINTAGE" in df_comparaison.columns:
            result_item["feriePointage"] = row["FERIE_POINTAGE"]
        if "FERIE_PAIE" in df_comparaison.columns:
            result_item["feriePaie"] = row["FERIE_PAIE"]
        if "HS25_POINTAGE" in df_comparaison.columns:
            result_item["hs25Pointage"] = row["HS25_POINTAGE"]
        if "HS25_PAIE" in df_comparaison.columns:
            result_item["hs25Paie"] = row["HS25_PAIE"]
            
        results.append(result_item)
    
    return {
        "results": results,
        "summary": {
            "total": len(results),
            "correct": sum(1 for r in results if r["status"] == "Correct"),
            "inconsistencies": sum(1 for r in results if r["status"] != "Correct"),
            "totalPrimeRendement": sum(r["primeRendement"] for r in results),
            "ferieInconsistencies": sum(1 for r in results if r.get("ferieStatus") == "Incohérence"),
            "hs25Inconsistencies": sum(1 for r in results if r.get("hs25Status") == "Incohérence")
        }
    }

    
if __name__ == '__main__':
    app.run(debug=True, port=8002)