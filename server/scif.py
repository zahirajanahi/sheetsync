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
        df_pointage = read_file_with_header(pointage_path, ["NOM ET PRÉNOM", "NORMAL"])
        df_paie = read_file_with_header(paie_path, ["NOM ET PRÉNOM", "JRS/HRS"])
    except ValueError as e:
        raise Exception(f"Erreur lors de la lecture des fichiers: {str(e)}")

    # Identify the correct columns
    name_col = next((col for col in df_pointage.columns if "NOM" in col and "PRÉNOM" in col), None)
    normal_col = next((col for col in df_pointage.columns if "NORMAL" in col), None)
    jrs_hrs_col = next((col for col in df_paie.columns if "JRS" in col or "HRS" in col), None)

    if not name_col or not normal_col:
        raise Exception(f"Colonnes introuvables dans Pointage. Colonnes disponibles: {df_pointage.columns.tolist()}")
    if not name_col or not jrs_hrs_col:
        raise Exception(f"Colonnes introuvables dans Journal de Paie. Colonnes disponibles: {df_paie.columns.tolist()}")

    # Clean and standardize names for better matching
    df_pointage[name_col] = df_pointage[name_col].astype(str).str.strip().str.upper()
    df_paie[name_col] = df_paie[name_col].astype(str).str.strip().str.upper()

    # Convert columns to numeric
    df_pointage[normal_col] = pd.to_numeric(df_pointage[normal_col], errors="coerce").fillna(0)
    df_paie[jrs_hrs_col] = pd.to_numeric(df_paie[jrs_hrs_col], errors="coerce").fillna(0)

    # Group pointage by name and sum the hours (to handle duplicate entries)
    df_pointage_grouped = df_pointage.groupby(name_col)[normal_col].sum().reset_index()
    df_pointage_grouped.columns = ["Nom_Complet", "Heures_Pointage"]

    # Prepare paie data
    df_paie = df_paie[[name_col, jrs_hrs_col]].rename(
        columns={name_col: "Nom_Complet", jrs_hrs_col: "Heures_Paie"}
    )

    # Merge on Nom_Complet
    df_comparaison = pd.merge(df_paie, df_pointage_grouped, on="Nom_Complet", how="outer").fillna(0)
    df_comparaison["Écart"] = df_comparaison["Heures_Pointage"] - df_comparaison["Heures_Paie"]

    # Generate results
    results = []
    for _, row in df_comparaison.iterrows():
        prime_rendement = 0
        status = "Incohérence"
        
        if row["Heures_Pointage"] == 0 and row["Heures_Paie"] > 0:
            status = "Employé absent dans pointage"
        elif row["Heures_Pointage"] > 0 and row["Heures_Paie"] == 0:
            status = "Heures non payées"
        elif row["Heures_Pointage"] > row["Heures_Paie"]:
            # Calculate Prime de Rendement when worked hours exceed paid hours
            prime_rendement = row["Heures_Pointage"] - row["Heures_Paie"]
            # If prime de rendement equals the difference, status is Correct
            if abs(prime_rendement - row["Écart"]) <= 0.01:
                status = "Correct"
        elif abs(row["Écart"]) <= 0.01:
            status = "Correct"

        results.append({
            "nomComplet": row["Nom_Complet"],
            "heuresTravaillees": row["Heures_Pointage"],
            "heuresPayees": row["Heures_Paie"],
            "difference": row["Écart"],
            "status": status,
            "primeRendement": prime_rendement
        })

    return {
        "results": results,
        "summary": {
            "total": len(results),
            "correct": sum(1 for r in results if r["status"] == "Correct"),
            "inconsistencies": sum(1 for r in results if r["status"] != "Correct"),
            "totalPrimeRendement": sum(r["primeRendement"] for r in results)
        }
    }

if __name__ == '__main__':
    app.run(debug=True, port=8001)