from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
from werkzeug.utils import secure_filename
from datetime import datetime

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
    
    # For the "HS 25" and "HS 50" columns in pointage
    hs25_pointage_col = next((col for col in df_pointage.columns if "HS 25" in col and "MT" not in col), None)
    hs50_pointage_col = next((col for col in df_pointage.columns if "HS 50" in col and "MT" not in col), None)
    
    # Paie file columns
    ncin_col_paie = next((col for col in df_paie.columns if "NCIN" in col or "CIN" in col), None)
    jrs_hrs_col_paie = next((col for col in df_paie.columns if "JRS" in col and "HRS" in col), None)
    
    # For the "HS 25" and "HS 50" columns in paie
    hs25_paie_col = next((col for col in df_paie.columns if "HS 25" in col and "MT" not in col), None)
    hs50_paie_col = next((col for col in df_paie.columns if "HS 50" in col and "MT" not in col), None)
            
    # New columns for paie validations
    acompte_col = next((col for col in df_paie.columns if "ACOMPTE" in col), None)
    net_paye_col = next((col for col in df_paie.columns if "NET" in col and "PAYE" in col), None)
    amo_col = next((col for col in df_paie.columns if "AMO" in col), None)
    cnss_col = next((col for col in df_paie.columns if "CNSS" in col), None)
    date_embauche_col = next((col for col in df_paie.columns if "DATE" in col and "EMBAUCHE" in col), None)
    
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
    
    # Convert validation columns to numeric if they exist
    if acompte_col:
        df_paie[acompte_col] = pd.to_numeric(df_paie[acompte_col], errors="coerce").fillna(0)
    if net_paye_col:
        df_paie[net_paye_col] = pd.to_numeric(df_paie[net_paye_col], errors="coerce").fillna(0)
    if amo_col:
        df_paie[amo_col] = pd.to_numeric(df_paie[amo_col], errors="coerce").fillna(0)
    if cnss_col:
        df_paie[cnss_col] = pd.to_numeric(df_paie[cnss_col], errors="coerce").fillna(0)
    
    # Convert HS 25 and HS 50 columns to numeric if they exist
    if hs25_pointage_col:
        df_pointage[hs25_pointage_col] = pd.to_numeric(df_pointage[hs25_pointage_col], errors="coerce").fillna(0)
    if hs25_paie_col:
        df_paie[hs25_paie_col] = pd.to_numeric(df_paie[hs25_paie_col], errors="coerce").fillna(0)
    if hs50_pointage_col:
        df_pointage[hs50_pointage_col] = pd.to_numeric(df_pointage[hs50_pointage_col], errors="coerce").fillna(0)
    if hs50_paie_col:
        df_paie[hs50_paie_col] = pd.to_numeric(df_paie[hs50_paie_col], errors="coerce").fillna(0)
    
    # Convert date_embauche to datetime if it exists
    if date_embauche_col:
        df_paie[date_embauche_col] = pd.to_datetime(df_paie[date_embauche_col], errors="coerce")
    
    # Group pointage by NCIN and aggregate data
    agg_dict = {
        jrs_hrs_col_pointage: 'sum'
    }
    
    if hs25_pointage_col:
        agg_dict[hs25_pointage_col] = 'sum'
    if hs50_pointage_col:
        agg_dict[hs50_pointage_col] = 'sum'
        
    df_pointage_grouped = df_pointage.groupby(ncin_col_pointage).agg(agg_dict).reset_index()
    
    # Rename columns for the grouped dataframe
    rename_dict_pointage = {
        ncin_col_pointage: "CIN",
        jrs_hrs_col_pointage: "Heures_Pointage"
    }
    
    if hs25_pointage_col:
        rename_dict_pointage[hs25_pointage_col] = "HS25_POINTAGE"
    if hs50_pointage_col:
        rename_dict_pointage[hs50_pointage_col] = "HS50_POINTAGE"
        
    df_pointage_grouped.rename(columns=rename_dict_pointage, inplace=True)
    
    # Prepare paie data
    paie_cols = [ncin_col_paie, jrs_hrs_col_paie]
    if hs25_paie_col:
        paie_cols.append(hs25_paie_col)
    if hs50_paie_col:
        paie_cols.append(hs50_paie_col)
    if acompte_col:
        paie_cols.append(acompte_col)
    if net_paye_col:
        paie_cols.append(net_paye_col)
    if amo_col:
        paie_cols.append(amo_col)
    if cnss_col:
        paie_cols.append(cnss_col)
    if date_embauche_col:
        paie_cols.append(date_embauche_col)
        
    rename_dict_paie = {
        ncin_col_paie: "CIN", 
        jrs_hrs_col_paie: "Heures_Paie"
    }
    
    if hs25_paie_col:
        rename_dict_paie[hs25_paie_col] = "HS25_PAIE"
    if hs50_paie_col:
        rename_dict_paie[hs50_paie_col] = "HS50_PAIE"
    if acompte_col:
        rename_dict_paie[acompte_col] = "ACOMPTE"
    if net_paye_col:
        rename_dict_paie[net_paye_col] = "NET_PAYE"
    if amo_col:
        rename_dict_paie[amo_col] = "AMO"
    if cnss_col:
        rename_dict_paie[cnss_col] = "CNSS"
    if date_embauche_col:
        rename_dict_paie[date_embauche_col] = "DATE_EMBAUCHE"
        
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
        
        # HS 50 comparison (HS 50 vs HS 50)
        hs50_status = "Correct"
        if "HS50_POINTAGE" in df_comparaison.columns and "HS50_PAIE" in df_comparaison.columns:
            if abs(row["HS50_POINTAGE"] - row["HS50_PAIE"]) > 0.01:
                hs50_status = "Incohérence"
                if status == "Correct":
                    status = "Incohérence"
                inconsistencies.append(f"HS 50 Pointage ({row['HS50_POINTAGE']}) ≠ HS 50 Paie ({row['HS50_PAIE']})")
        elif "HS50_POINTAGE" in df_comparaison.columns and row["HS50_POINTAGE"] > 0:
            hs50_status = "Incohérence"
            if status == "Correct":
                status = "Incohérence"
            inconsistencies.append(f"HS 50 Pointage ({row['HS50_POINTAGE']}) mais absent dans Paie")
        elif "HS50_PAIE" in df_comparaison.columns and row["HS50_PAIE"] > 0:
            hs50_status = "Incohérence"
            if status == "Correct":
                status = "Incohérence"
            inconsistencies.append(f"HS 50 Paie ({row['HS50_PAIE']}) mais absent dans Pointage")
        
        # New: Paie validations
        paie_validations = {}
        
        # AMO & CNSS Check
        amo_cnss_check = {"status": "Valid"}  # Default to Valid
        if "AMO" in df_comparaison.columns and "CNSS" in df_comparaison.columns:
            amo = float(row["AMO"]) if pd.notna(row["AMO"]) else 0
            cnss = float(row["CNSS"]) if pd.notna(row["CNSS"]) else 0
            
            amo_cnss_check = {
                "amo": amo,
                "cnss": cnss,
                "status": "Valid" if amo > 0 and cnss > 0 else "Employé non déclaré"
            }
        paie_validations["amoCnssCheck"] = amo_cnss_check
        
        # Date d'Embauche Check with updated contract duration logic
        embauche_date_check = {"status": "Valid"}  # Default to Valid
        if "DATE_EMBAUCHE" in df_comparaison.columns and pd.notna(row["DATE_EMBAUCHE"]):
            try:
                date_embauche = pd.to_datetime(row["DATE_EMBAUCHE"])
                today = pd.to_datetime('today')
                anciennete = (today - date_embauche).days / 30  # Convert to months
                
                embauche_date_check = {
                    "dateEmbauche": date_embauche.strftime('%Y-%m-%d') if not pd.isna(date_embauche) else "Non spécifiée",
                    "anciennete": f"{anciennete:.1f} mois",
                    "status": "Fin de Contrat" if anciennete > 5 else "Valide"
                }
            except Exception as e:
                embauche_date_check = {
                    "dateEmbauche": "Format invalide",
                    "anciennete": "Non calculée",
                    "status": "Non vérifié",
                    "error": str(e)
                }
                
        paie_validations["embaucheDateCheck"] = embauche_date_check
        
        result_item = {
            "CIN": row["CIN"],
            "heuresTravaillees": row["Heures_Pointage"],
            "heuresPayees": row["Heures_Paie"],
            "difference": row["Écart"],
            "status": status,
            "primeRendement": prime_rendement,
            "hs25Status": hs25_status,
            "hs50Status": hs50_status,
            "inconsistencies": inconsistencies,
            "paieValidations": paie_validations
        }
        
        # Add optional fields if they exist in the dataframe
        if "HS25_POINTAGE" in df_comparaison.columns:
            result_item["hs25Pointage"] = row["HS25_POINTAGE"]
        if "HS25_PAIE" in df_comparaison.columns:
            result_item["hs25Paie"] = row["HS25_PAIE"]
        if "HS50_POINTAGE" in df_comparaison.columns:
            result_item["hs50Pointage"] = row["HS50_POINTAGE"]
        if "HS50_PAIE" in df_comparaison.columns:
            result_item["hs50Paie"] = row["HS50_PAIE"]
        if "ACOMPTE" in df_comparaison.columns:
            result_item["acompte"] = row["ACOMPTE"]
        if "NET_PAYE" in df_comparaison.columns:
            result_item["netPaye"] = row["NET_PAYE"]
        if "AMO" in df_comparaison.columns:
            result_item["amo"] = row["AMO"]
        if "CNSS" in df_comparaison.columns:
            result_item["cnss"] = row["CNSS"]
        if "DATE_EMBAUCHE" in df_comparaison.columns:
            # Format date as string for JSON serialization if it's a datetime
            if isinstance(row["DATE_EMBAUCHE"], pd.Timestamp):
                result_item["dateEmbauche"] = row["DATE_EMBAUCHE"].strftime('%Y-%m-%d')
            else:
                result_item["dateEmbauche"] = row["DATE_EMBAUCHE"]
            
        results.append(result_item)
    
    return {
        "results": results,
        "summary": {
            "total": len(results),
            "correct": sum(1 for r in results if r["status"] == "Correct"),
            "inconsistencies": sum(1 for r in results if r["status"] != "Correct"),
            "totalPrimeRendement": sum(r["primeRendement"] for r in results),
            "hs25Inconsistencies": sum(1 for r in results if r.get("hs25Status") == "Incohérence"),
            "hs50Inconsistencies": sum(1 for r in results if r.get("hs50Status") == "Incohérence")
        }
    }

if __name__ == '__main__':
    app.run(debug=True, port=8006)