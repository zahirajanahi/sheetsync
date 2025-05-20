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
        # Pointage uses CIN, Journal de Paie uses NCIN
        df_pointage = read_file_with_header(pointage_path, ["CIN", "NORMAL"])
        df_paie = read_file_with_header(paie_path, ["NCIN", "JRS/HRS"])
    except ValueError as e:
        raise Exception(f"Erreur lors de la lecture des fichiers: {str(e)}")
    
    # Print column names for debugging
    print("Pointage columns:", df_pointage.columns.tolist())
    print("Paie columns:", df_paie.columns.tolist())
    
    # Identify the correct columns - using more flexible matching
    cin_col_pointage = next((col for col in df_pointage.columns if "CIN" in col), None)
    normal_col = next((col for col in df_pointage.columns if "NORMAL" in col), None)
    taux_col = next((col for col in df_pointage.columns if "TAUX" in col and "HORA" in col), None)
    
    # For the "jour férié" column in pointage - simplified approach
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
            
    # Find the 25% column in pointage
    pct25_pointage_col = None
    for col in df_pointage.columns:
        if "25%" in col:
            pct25_pointage_col = col
            break
            
    if not pct25_pointage_col:
        print("Warning: Could not find 25% column in pointage file!")
        print("Available columns:", df_pointage.columns.tolist())
        
    ncin_col_paie = next((col for col in df_paie.columns if "NCIN" in col or "CIN" in col), None)
    jrs_hrs_col = next((col for col in df_paie.columns if "JRS" in col or "HRS" in col), None)
    salaire_col = next((col for col in df_paie.columns if "SALAIRE" in col), None)
    
    # For the "Férié" column in paie - simplified approach
    ferie_paie_col = None
    for col in df_paie.columns:
        if "FERIE" in col or "FÉRIÉ" in col:
            ferie_paie_col = col
            break
    
    # Find HS 25 column in paie
    hs25_paie_col = None
    for col in df_paie.columns:
        if "HS 25" in col and "MT" not in col:  # Exclude MT HS 25
            hs25_paie_col = col
            break
            
    # Find MT HS 25 column in paie
    mt_hs25_paie_col = None
    for col in df_paie.columns:
        if "MT HS 25" in col:
            mt_hs25_paie_col = col
            break
            
    # ADDED: Find AMO column in paie
    amo_col = next((col for col in df_paie.columns if "AMO" in col), None)
    
    # ADDED: Find CNSS column in paie
    cnss_col = next((col for col in df_paie.columns if "CNSS" in col), None)
    
    # ADDED: Find DATE EMBAUCHE column in paie
    date_embauche_col = next((col for col in df_paie.columns if "DATE" in col and "EMBAUCHE" in col), None)
    
    if not hs25_paie_col:
        print("Warning: Could not find HS 25 column in paie file!")
        print("Available columns:", df_paie.columns.tolist())
        
    if not mt_hs25_paie_col:
        print("Warning: Could not find MT HS 25 column in paie file!")
        print("Available columns:", df_paie.columns.tolist())
        
    # Check required columns
    required_pointage_cols = {
        "CIN": cin_col_pointage,
        "NORMAL": normal_col
    }
    required_paie_cols = {
        "NCIN": ncin_col_paie,
        "JRS/HRS": jrs_hrs_col
    }
    missing_pointage = [k for k, v in required_pointage_cols.items() if not v]
    missing_paie = [k for k, v in required_paie_cols.items() if not v]
    if missing_pointage:
        raise Exception(f"Colonnes manquantes dans Pointage: {', '.join(missing_pointage)}. Colonnes disponibles: {df_pointage.columns.tolist()}")
    if missing_paie:
        raise Exception(f"Colonnes manquantes dans Journal de Paie: {', '.join(missing_paie)}. Colonnes disponibles: {df_paie.columns.tolist()}")
        
    # Clean and standardize CIN/NCIN for better matching
    df_pointage[cin_col_pointage] = df_pointage[cin_col_pointage].astype(str).str.strip().str.upper()
    df_paie[ncin_col_paie] = df_paie[ncin_col_paie].astype(str).str.strip().str.upper()
    
    # Filter out rows with empty/NaN CIN values in Journal de Paie
    df_paie = df_paie[df_paie[ncin_col_paie].str.strip() != '']
    df_paie = df_paie[df_paie[ncin_col_paie] != 'NAN']
    df_paie = df_paie[df_paie[ncin_col_paie] != 'N/A']
    
    # Convert columns to numeric
    df_pointage[normal_col] = pd.to_numeric(df_pointage[normal_col], errors="coerce").fillna(0)
    df_paie[jrs_hrs_col] = pd.to_numeric(df_paie[jrs_hrs_col], errors="coerce").fillna(0)
    
    # Convert ferié columns to numeric if they exist
    if ferie_pointage_col:
        df_pointage[ferie_pointage_col] = pd.to_numeric(df_pointage[ferie_pointage_col], errors="coerce").fillna(0)
    if ferie_paie_col:
        df_paie[ferie_paie_col] = pd.to_numeric(df_paie[ferie_paie_col], errors="coerce").fillna(0)
    
    # Convert 25% columns to numeric if they exist
    if pct25_pointage_col:
        df_pointage[pct25_pointage_col] = pd.to_numeric(df_pointage[pct25_pointage_col], errors="coerce").fillna(0)
    if hs25_paie_col:
        df_paie[hs25_paie_col] = pd.to_numeric(df_paie[hs25_paie_col], errors="coerce").fillna(0)
    if mt_hs25_paie_col:
        df_paie[mt_hs25_paie_col] = pd.to_numeric(df_paie[mt_hs25_paie_col], errors="coerce").fillna(0)
    
    # Convert other columns to numeric if they exist
    if taux_col:
        df_pointage[taux_col] = pd.to_numeric(df_pointage[taux_col], errors="coerce").fillna(0)
    if salaire_col:
        df_paie[salaire_col] = pd.to_numeric(df_paie[salaire_col], errors="coerce").fillna(0)
    
    # ADDED: Convert AMO and CNSS columns to numeric if they exist
    if amo_col:
        df_paie[amo_col] = pd.to_numeric(df_paie[amo_col], errors="coerce").fillna(0)
    if cnss_col:
        df_paie[cnss_col] = pd.to_numeric(df_paie[cnss_col], errors="coerce").fillna(0)
    
    # ADDED: Convert date_embauche to datetime if it exists
    if date_embauche_col:
        df_paie[date_embauche_col] = pd.to_datetime(df_paie[date_embauche_col], errors="coerce")
    
    # Group pointage by CIN and aggregate data
    agg_dict = {normal_col: 'sum'}
    
    if taux_col:
        agg_dict[taux_col] = 'first'  # Use first instead of including in group_cols
    if ferie_pointage_col:
        agg_dict[ferie_pointage_col] = 'sum'
    if pct25_pointage_col:
        agg_dict[pct25_pointage_col] = 'sum'
        
    df_pointage_grouped = df_pointage.groupby(cin_col_pointage).agg(agg_dict).reset_index()
    
    # Rename columns for the grouped dataframe
    rename_dict_pointage = {
        cin_col_pointage: "CIN",
        normal_col: "Heures_Pointage"
    }
    
    if taux_col:
        rename_dict_pointage[taux_col] = "TAUX_HORAIRE"
    if ferie_pointage_col:
        rename_dict_pointage[ferie_pointage_col] = "FERIE_POINTAGE"
    if pct25_pointage_col:
        rename_dict_pointage[pct25_pointage_col] = "PCT25_POINTAGE"
        
    df_pointage_grouped.rename(columns=rename_dict_pointage, inplace=True)
    
    # Prepare paie data
    paie_cols = [ncin_col_paie, jrs_hrs_col]
    if salaire_col:
        paie_cols.append(salaire_col)
    if ferie_paie_col:
        paie_cols.append(ferie_paie_col)
    if hs25_paie_col:
        paie_cols.append(hs25_paie_col)
    if mt_hs25_paie_col:
        paie_cols.append(mt_hs25_paie_col)
    # ADDED: Include AMO, CNSS, and DATE_EMBAUCHE columns if they exist
    if amo_col:
        paie_cols.append(amo_col)
    if cnss_col:
        paie_cols.append(cnss_col)
    if date_embauche_col:
        paie_cols.append(date_embauche_col)
        
    rename_dict_paie = {
        ncin_col_paie: "CIN", 
        jrs_hrs_col: "Heures_Paie"
    }
    
    if salaire_col:
        rename_dict_paie[salaire_col] = "Salaire_Paie"
    if ferie_paie_col:
        rename_dict_paie[ferie_paie_col] = "FERIE_PAIE"
    if hs25_paie_col:
        rename_dict_paie[hs25_paie_col] = "HS25_PAIE"
    if mt_hs25_paie_col:
        rename_dict_paie[mt_hs25_paie_col] = "MT_HS25_PAIE"
    # ADDED: Rename AMO, CNSS, and DATE_EMBAUCHE columns
    if amo_col:
        rename_dict_paie[amo_col] = "AMO"
    if cnss_col:
        rename_dict_paie[cnss_col] = "CNSS"
    if date_embauche_col:
        rename_dict_paie[date_embauche_col] = "DATE_EMBAUCHE"
        
    df_paie = df_paie[paie_cols].rename(columns=rename_dict_paie)
    
    # Merge on CIN
    df_comparaison = pd.merge(df_paie, df_pointage_grouped, on="CIN", how="outer").fillna(0)
    df_comparaison["Écart"] = df_comparaison["Heures_Pointage"] - df_comparaison["Heures_Paie"]
    
    # Calculate expected MT HS 25 if we have all required columns
    if "HS25_PAIE" in df_comparaison.columns and "TAUX_HORAIRE" in df_comparaison.columns:
        df_comparaison["MT_HS25_EXPECTED"] = df_comparaison["HS25_PAIE"] * df_comparaison["TAUX_HORAIRE"] * 1.25
    
    # Print columns in the comparison dataframe for debugging
    print("Columns in comparison dataframe:", df_comparaison.columns.tolist())
    
    # Generate results
    results = []
    for _, row in df_comparaison.iterrows():
        # Skip rows with empty/NaN CIN values in the final results
        if pd.isna(row["CIN"]) or str(row["CIN"]).strip() in ['', 'NAN', 'N/A']:
            continue
            
        prime_rendement = 0
        status = "Incohérence"
        inconsistencies = []
        
        # Hours comparison
        if row["Heures_Pointage"] == 0 and row["Heures_Paie"] > 0:
            status = "Employé absent dans pointage"
            inconsistencies.append("Heures: Employé absent dans pointage")
        elif row["Heures_Pointage"] > 0 and row["Heures_Paie"] == 0:
            status = "Employé absent dans journal de paie"
            inconsistencies.append("Heures: Employé absent dans journal de paie")
        elif row["Heures_Pointage"] > row["Heures_Paie"]:
            # Calculate Prime de Rendement when worked hours exceed paid hours
            prime_rendement = row["Heures_Pointage"] - row["Heures_Paie"]
            # If prime de rendement equals the difference, status is Correct
            if abs(prime_rendement - row["Écart"]) <= 0.01:
                status = "Correct"
        elif abs(row["Écart"]) <= 0.01:
            status = "Correct"
        
        # TAUX Horaire vs Salaire comparison - They should be exactly equal
        taux_salaire_status = "Correct"
        if "TAUX_HORAIRE" in df_comparaison.columns and "Salaire_Paie" in df_comparaison.columns:
            if abs(row["TAUX_HORAIRE"] - row["Salaire_Paie"]) > 0.01:
                taux_salaire_status = "Incohérence"
                if status == "Correct":
                    status = "Incohérence"
                inconsistencies.append(f"TAUX Horaire ({row['TAUX_HORAIRE']}) ≠ Salaire ({row['Salaire_Paie']}) - Devraient être identiques")
        
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
            inconsistencies.append(f"Férié Pointage ({row['FERIE_POINTAGE']}) mais absent dans Paie")
        elif "FERIE_PAIE" in df_comparaison.columns and row["FERIE_PAIE"] > 0:
            ferie_status = "Incohérence"
            inconsistencies.append(f"Férié Paie ({row['FERIE_PAIE']}) mais absent dans Pointage")
        
        # 25% comparison
        pct25_status = "Correct"
        if "PCT25_POINTAGE" in df_comparaison.columns and "HS25_PAIE" in df_comparaison.columns:
            if abs(row["PCT25_POINTAGE"] - row["HS25_PAIE"]) > 0.01:
                pct25_status = "Incohérence"
                if status == "Correct":
                    status = "Incohérence"
                inconsistencies.append(f"25% Pointage ({row['PCT25_POINTAGE']}) ≠ HS 25 Paie ({row['HS25_PAIE']})")
        elif "PCT25_POINTAGE" in df_comparaison.columns and row["PCT25_POINTAGE"] > 0:
            pct25_status = "Incohérence"
            inconsistencies.append(f"25% Pointage ({row['PCT25_POINTAGE']}) mais absent dans Paie")
        elif "HS25_PAIE" in df_comparaison.columns and row["HS25_PAIE"] > 0:
            pct25_status = "Incohérence"
            inconsistencies.append(f"HS 25 Paie ({row['HS25_PAIE']}) mais absent dans Pointage")
        
        # MT HS 25 calculation check
        mt_hs25_status = "Correct"
        if "MT_HS25_PAIE" in df_comparaison.columns and "MT_HS25_EXPECTED" in df_comparaison.columns:
            if row["HS25_PAIE"] > 0 and abs(row["MT_HS25_PAIE"] - row["MT_HS25_EXPECTED"]) > 0.01:
                mt_hs25_status = "Incohérence"
                if status == "Correct":
                    status = "Incohérence"
                inconsistencies.append(f"MT HS 25 ({row['MT_HS25_PAIE']}) ≠ HS 25 * TAUX * 1.25 ({row['MT_HS25_EXPECTED']})")
        
        # ADDED: Paie validations
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
            "tauxSalaireStatus": taux_salaire_status,
            "ferieStatus": ferie_status,
            "pct25Status": pct25_status,
            "mtHs25Status": mt_hs25_status,
            "inconsistencies": inconsistencies,
            "paieValidations": paie_validations  # ADDED: Include paie validations
        }
        
        # Add optional fields if they exist in the dataframe
        if "TAUX_HORAIRE" in df_comparaison.columns:
            result_item["tauxHoraire"] = row["TAUX_HORAIRE"]
        if "Salaire_Paie" in df_comparaison.columns:
            result_item["salairePaie"] = row["Salaire_Paie"]
        if "FERIE_POINTAGE" in df_comparaison.columns:
            result_item["feriePointage"] = row["FERIE_POINTAGE"]
        if "FERIE_PAIE" in df_comparaison.columns:
            result_item["feriePaie"] = row["FERIE_PAIE"]
        if "PCT25_POINTAGE" in df_comparaison.columns:
            result_item["pct25Pointage"] = row["PCT25_POINTAGE"]
        if "HS25_PAIE" in df_comparaison.columns:
            result_item["hs25Paie"] = row["HS25_PAIE"]
        if "MT_HS25_PAIE" in df_comparaison.columns:
            result_item["mtHs25Paie"] = row["MT_HS25_PAIE"]
        if "MT_HS25_EXPECTED" in df_comparaison.columns:
            result_item["mtHs25Expected"] = row["MT_HS25_EXPECTED"]
        # ADDED: Include AMO, CNSS, and DATE_EMBAUCHE fields if they exist
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
            "tauxSalaireInconsistencies": sum(1 for r in results if r.get("tauxSalaireStatus") == "Incohérence"),
            "ferieInconsistencies": sum(1 for r in results if r.get("ferieStatus") == "Incohérence"),
            "pct25Inconsistencies": sum(1 for r in results if r.get("pct25Status") == "Incohérence"),
            "mtHs25Inconsistencies": sum(1 for r in results if r.get("mtHs25Status") == "Incohérence")
        }
    }

if __name__ == '__main__':
    app.run(debug=True, port=8001)