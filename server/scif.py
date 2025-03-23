from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
import numpy as np
from werkzeug.utils import secure_filename

app = Flask(__name__)
# Configuration plus explicite de CORS
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "Backend is working"}), 200

@app.route('/upload', methods=['POST'])
def upload_files():
    print("Requête reçue sur /upload")
    
    if 'pointage' not in request.files or 'paie' not in request.files:
        print("Erreur: Fichiers manquants")
        return jsonify({'error': 'Les deux fichiers sont requis'}), 400
    
    pointage_file = request.files['pointage']
    paie_file = request.files['paie']
    
    if pointage_file.filename == '' or paie_file.filename == '':
        print("Erreur: Noms de fichiers vides")
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400
    
    # Save files
    pointage_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(pointage_file.filename))
    paie_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(paie_file.filename))
    
    pointage_file.save(pointage_path)
    paie_file.save(paie_path)
    
    # Process files
    try:
        print("Traitement des fichiers...")
        comparison_results = compare_files(pointage_path, paie_path)
        return jsonify(comparison_results), 200
    except Exception as e:
        print(f"Erreur lors du traitement: {str(e)}")
        return jsonify({'error': str(e)}), 500

def preprocess_pointage_file(file_path):
    """Prétraite le fichier de pointage pour extraire les données pertinentes"""
    # Charger tout le fichier sans en-têtes spécifiques
    df = pd.read_excel(file_path, header=None)
    print(f"Dimensions du fichier de pointage brut: {df.shape}")
    
    # Chercher les en-têtes pertinentes
    cin_col = None
    name_col = None
    hours_col = None
    
    # Rechercher les indices de ligne et colonne où se trouvent les en-têtes
    header_row = None
    for i in range(min(20, len(df))):  # Examiner les 20 premières lignes
        row = df.iloc[i].astype(str)
        row_values = [str(val).upper() for val in row.values]
        
        # Chercher des indices d'une ligne d'en-tête
        if any(x in row_values for x in ['NOM', 'PRÉNOM', 'CIN', 'MATRICULE']):
            header_row = i
            print(f"Ligne d'en-tête trouvée à la ligne {i}: {row_values}")
            
            # Identifier les colonnes
            for j, val in enumerate(row_values):
                if 'CIN' in val or 'MATRICULE' in val:
                    cin_col = j
                    print(f"Colonne CIN trouvée à l'index {j}: {val}")
                elif 'NOM' in val or 'PRENOM' in val or 'PRÉNOM' in val:
                    name_col = j
                    print(f"Colonne Nom trouvée à l'index {j}: {val}")
                elif 'NORMAL' in val or 'HEURE' in val or 'TOTAL' in val:
                    hours_col = j
                    print(f"Colonne des heures trouvée à l'index {j}: {val}")
            
            # Si on a trouvé au moins deux des colonnes, on considère que c'est une ligne d'en-tête valide
            if (cin_col is not None and hours_col is not None) or (cin_col is not None and name_col is not None):
                break
                
    # Si on n'a pas trouvé d'en-tête, chercher des colonnes qui semblent contenir des données pertinentes
    if header_row is None:
        print("Aucune ligne d'en-tête trouvée. Recherche alternative de données...")
        
        # Parcourir toutes les colonnes pour trouver celles qui pourraient contenir des CIN et des heures
        for col in range(df.shape[1]):
            col_values = df.iloc[:, col].astype(str)
            # Chercher une colonne qui ressemble à des CIN (format commun: lettres ou chiffres, au moins 5-8 caractères)
            if col_values.str.match(r'^[A-Za-z0-9]{5,8}$').any():
                cin_col = col
                print(f"Colonne potentielle de CIN trouvée à l'index {col}")
            # Chercher une colonne qui contient principalement des valeurs numériques qui pourraient être des heures
            elif col_values.str.replace('.', '', regex=True).str.isnumeric().mean() > 0.5:
                numeric_values = pd.to_numeric(col_values, errors='coerce')
                if numeric_values.mean() > 0 and numeric_values.mean() < 200:  # Valeurs plausibles pour des heures
                    hours_col = col
                    print(f"Colonne potentielle d'heures trouvée à l'index {col}")
    
    if cin_col is None or hours_col is None:
        # Dernier recours: extraire des données du fichier Excel original avec plus d'infos visuelles
        print("Tentative de récupération des données à partir du fichier avec formatage...")
        try:
            # Essayer de charger le fichier avec un parser différent
            xls = pd.ExcelFile(file_path)
            df = pd.read_excel(xls, header=None)
            
            # Imprimer toutes les valeurs uniques de chaque colonne pour aider au débogage
            for col in range(min(df.shape[1], 10)):  # Limiter aux 10 premières colonnes pour éviter trop de sortie
                unique_vals = df.iloc[:, col].dropna().unique()
                if len(unique_vals) > 0 and len(unique_vals) < 10:  # N'afficher que s'il y a un nombre raisonnable de valeurs
                    print(f"Colonne {col} valeurs uniques: {unique_vals}")
            
            # Rechercher des mots-clés dans tout le fichier
            for i in range(min(df.shape[0], 50)):  # Limiter aux 50 premières lignes
                for j in range(min(df.shape[1], 20)):  # Limiter aux 20 premières colonnes
                    val = str(df.iloc[i, j]).upper()
                    if 'NORMAL' in val:
                        print(f"Mot-clé 'NORMAL' trouvé à la position ({i}, {j}): {val}")
                    if 'CIN' in val:
                        print(f"Mot-clé 'CIN' trouvé à la position ({i}, {j}): {val}")
                    if 'HEURE' in val:
                        print(f"Mot-clé 'HEURE' trouvé à la position ({i}, {j}): {val}")
        except Exception as e:
            print(f"Erreur lors de la tentative de récupération: {str(e)}")
        
        raise Exception("Impossible de déterminer la structure du fichier de pointage. Veuillez vérifier le format du fichier.")
    
    # Si on a trouvé une ligne d'en-tête, extraire les données à partir de cette ligne
    if header_row is not None:
        data_df = df.iloc[header_row+1:].copy()  # Prendre toutes les lignes après l'en-tête
        data_df.columns = df.iloc[header_row]    # Utiliser la ligne d'en-tête comme noms de colonnes
    else:
        # Sinon, utiliser les colonnes trouvées pour créer un nouveau DataFrame
        data_df = pd.DataFrame()
        data_df['CIN'] = df.iloc[:, cin_col]
        data_df['NORMAL'] = df.iloc[:, hours_col]
        if name_col is not None:
            data_df['Nom'] = df.iloc[:, name_col]
    
    # Nettoyer les données
    data_df = data_df.dropna(subset=['CIN', 'NORMAL'])  # Supprimer les lignes sans CIN ou heures
    data_df['NORMAL'] = pd.to_numeric(data_df['NORMAL'], errors='coerce')
    
    print(f"Données extraites du fichier de pointage: {data_df.shape[0]} lignes")
    return data_df

def compare_files(pointage_path, paie_path):
    # Prétraiter le fichier de pointage
    print("Prétraitement du fichier pointage...")
    try:
        df_pointage = preprocess_pointage_file(pointage_path)
    except Exception as e:
        print(f"Erreur lors du prétraitement du fichier pointage: {str(e)}")
        # Si le prétraitement échoue, essayer avec la méthode standard
        df_pointage = pd.read_excel(pointage_path)
        # Tenter de trouver une ligne qui contient "CIN" et "NORMAL"
        for i in range(min(20, len(df_pointage))):
            row = df_pointage.iloc[i].astype(str)
            if 'CIN' in row.values and any('NORMAL' in str(val) for val in row.values):
                # Utiliser cette ligne comme en-tête
                df_pointage = pd.read_excel(pointage_path, header=i)
                break
    
    print(f"Colonnes du fichier pointage après prétraitement: {df_pointage.columns.tolist()}")
    
    print("Lecture du fichier paie...")
    # D'abord, chercher la ligne d'en-tête dans le fichier de paie
    df_temp = pd.read_excel(paie_path, header=None)
    header_row = None
    
    # Chercher des mots-clés dans les 30 premières lignes
    for i in range(min(30, len(df_temp))):
        row_values = [str(val).upper() for val in df_temp.iloc[i].values]
        # Chercher des indices d'une ligne d'en-tête comme 'MATRICULE', 'CIN', etc.
        if any(keyword in ' '.join(row_values) for keyword in ['MATRICULE', 'CIN', 'JRS', 'HRS', 'HEURE']):
            header_row = i
            print(f"Possible ligne d'en-tête trouvée dans le fichier paie à la ligne {i}: {row_values}")
            break
    
    # Lire le fichier avec l'en-tête identifié
    if header_row is not None:
        df_paie = pd.read_excel(paie_path, header=header_row)
    else:
        # Si aucun en-tête n'est trouvé, lire sans en-tête et traiter manuellement
        df_paie = pd.read_excel(paie_path, header=None)
    
    print(f"Colonnes dans le fichier paie: {df_paie.columns.tolist()}")
    
    # Identifier les colonnes pertinentes dans le fichier de paie
    matricule_col = None
    hrs_col = None
    
    # Recherche de colonnes par nom
    for col in df_paie.columns:
        col_str = str(col).lower()
        # Chercher la colonne de matricule
        if 'matricule' in col_str or 'cin' in col_str:
            matricule_col = col
            print(f"Colonne de matricule identifiée: {col}")
        # Chercher la colonne d'heures
        elif 'hrs' in col_str or 'jrs' in col_str or 'heure' in col_str:
            hrs_col = col
            print(f"Colonne d'heures identifiée: {col}")
    
    # Si les colonnes n'ont pas été trouvées par nom, essayer d'analyser le contenu
    if matricule_col is None or hrs_col is None:
        print("Recherche des colonnes par contenu...")
        
        # Parcourir toutes les colonnes pour trouver celles qui correspondent à nos critères
        for col in df_paie.columns:
            # Convertir la colonne en chaînes de caractères
            col_values = df_paie[col].astype(str)
            
            # Chercher une colonne qui ressemble à des identifiants (matricules/CIN)
            if matricule_col is None:
                # Vérifier si la colonne contient des identifiants textuels ou numériques
                if col_values.str.match(r'^[A-Za-z0-9]{5,8}$').mean() > 0.5:  # Format typique d'un matricule ou CIN
                    matricule_col = col
                    print(f"Colonne potentielle de matricule trouvée: {col}")
            
            # Chercher une colonne qui contient principalement des valeurs numériques qui pourraient être des heures
            if hrs_col is None:
                try:
                    numeric_values = pd.to_numeric(col_values, errors='coerce')
                    # Vérifier si les valeurs sont dans une plage typique d'heures de travail (0-200)
                    if numeric_values.dropna().mean() > 0 and numeric_values.dropna().mean() < 200:
                        hrs_col = col
                        print(f"Colonne potentielle d'heures trouvée: {col}")
                except:
                    pass
    
    # Si toujours pas trouvé, prendre les premières colonnes non vides comme dernier recours
    if matricule_col is None:
        for col in df_paie.columns:
            if df_paie[col].notna().sum() > df_paie.shape[0] * 0.5:  # Au moins 50% de valeurs non NA
                matricule_col = col
                print(f"Utilisation de la colonne non vide comme matricule: {col}")
                break
    
    if hrs_col is None:
        for col in df_paie.columns:
            if col != matricule_col and df_paie[col].notna().sum() > df_paie.shape[0] * 0.5:
                # Vérifier si la colonne contient des valeurs numériques
                if pd.to_numeric(df_paie[col], errors='coerce').notna().sum() > 0:
                    hrs_col = col
                    print(f"Utilisation de la colonne numérique non vide comme heures: {col}")
                    break
    
    # Si nous n'avons toujours pas trouvé les colonnes nécessaires, lever une exception
    if matricule_col is None:
        raise Exception(f"Impossible de trouver une colonne 'Matricule' dans le fichier de paie. Colonnes disponibles: {df_paie.columns.tolist()}")
    
    if hrs_col is None:
        raise Exception(f"Impossible de trouver une colonne 'Jrs/Hrs' dans le fichier de paie. Colonnes disponibles: {df_paie.columns.tolist()}")
    
    # Renommer les colonnes pour la cohérence
    df_paie = df_paie.rename(columns={matricule_col: 'Matricule', hrs_col: 'Jrs/Hrs'})
    
    # Ensure required columns exist in pointage
    if 'CIN' not in df_pointage.columns:
        cin_cols = [col for col in df_pointage.columns if 'cin' in str(col).lower()]
        if cin_cols:
            df_pointage = df_pointage.rename(columns={cin_cols[0]: 'CIN'})
        else:
            raise Exception(f"Fichier de pointage doit contenir une colonne identifiable comme 'CIN'. Colonnes trouvées: {df_pointage.columns.tolist()}")
    
    if 'NORMAL' not in df_pointage.columns:
        normal_cols = [col for col in df_pointage.columns if 'normal' in str(col).lower() or 'heure' in str(col).lower() or 'total' in str(col).lower()]
        if normal_cols:
            df_pointage = df_pointage.rename(columns={normal_cols[0]: 'NORMAL'})
        else:
            raise Exception(f"Fichier de pointage doit contenir une colonne identifiable comme 'NORMAL'. Colonnes trouvées: {df_pointage.columns.tolist()}")
    
    # Convertir les colonnes en numérique si nécessaire
    df_pointage['NORMAL'] = pd.to_numeric(df_pointage['NORMAL'], errors='coerce')
    df_paie['Jrs/Hrs'] = pd.to_numeric(df_paie['Jrs/Hrs'], errors='coerce')
    
    # Nettoyer les valeurs de CIN et Matricule pour s'assurer qu'elles sont comparables
    df_pointage['CIN'] = df_pointage['CIN'].astype(str).str.strip()
    df_paie['Matricule'] = df_paie['Matricule'].astype(str).str.strip()
    
    # Supprimer les lignes où le matricule est invalide (NaN, vide, etc.)
    df_paie = df_paie[df_paie['Matricule'].notna() & (df_paie['Matricule'] != 'nan') & (df_paie['Matricule'] != '')]
    df_pointage = df_pointage[df_pointage['CIN'].notna() & (df_pointage['CIN'] != 'nan') & (df_pointage['CIN'] != '')]
    
    # Prepare results
    results = []
    
    # For each employee in the paie journal
    for _, paie_row in df_paie.iterrows():
        matricule = paie_row['Matricule']
        jrs_hrs = paie_row['Jrs/Hrs']
        
        if pd.isna(jrs_hrs):
            jrs_hrs = 0
        
        # Try to find the corresponding employee in pointage
        matching_pointage = df_pointage[df_pointage['CIN'] == matricule]
        
        if not matching_pointage.empty:
            # Employee found
            normal_hours = matching_pointage['NORMAL'].iloc[0]
            
            if pd.isna(normal_hours):
                normal_hours = 0
                
            difference = normal_hours - jrs_hrs
            
            results.append({
                'matricule': matricule,
                'heuresTravaillees': float(normal_hours),
                'heuresPayees': float(jrs_hrs),
                'difference': float(difference),
                'status': 'Incohérence' if abs(difference) > 0.01 else 'Correct'
            })
        else:
            # Employee not found in pointage file
            results.append({
                'matricule': matricule,
                'heuresTravaillees': 0,
                'heuresPayees': float(jrs_hrs),
                'difference': -float(jrs_hrs),
                'status': 'Employé absent dans pointage'
            })
    
    # Check for employees in pointage but not in paie
    for _, pointage_row in df_pointage.iterrows():
        cin = pointage_row['CIN']
        normal_hours = pointage_row['NORMAL']
        
        if pd.isna(normal_hours):
            normal_hours = 0
        
        if not any(str(result['matricule']) == str(cin) for result in results):
            results.append({
                'matricule': str(cin),
                'heuresTravaillees': float(normal_hours),
                'heuresPayees': 0,
                'difference': float(normal_hours),
                'status': 'Heures non payées'
            })
    
    return {
        'results': results,
        'summary': {
            'total': len(results),
            'correct': sum(1 for r in results if r['status'] == 'Correct'),
            'inconsistencies': sum(1 for r in results if r['status'] != 'Correct')
        }
    }

if __name__ == '__main__':
    app.run(debug=True, port=8001)