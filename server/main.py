from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route('/api/compare', methods=['POST'])
def compare():
    try:
        if 'timesheet' not in request.files or 'payroll' not in request.files:
            return jsonify({
                'error': 'Les deux fichiers sont requis'
            }), 400
        timesheet_file = request.files['timesheet']
        payroll_file = request.files['payroll']

        # Lire les fichiers Excel avec pandas
        try:
            # Lire le fichier de pointage
            timesheet_df = pd.read_excel(BytesIO(timesheet_file.read()))

            # Lire le fichier de journal de paie 
            payroll_df = pd.read_excel(BytesIO(payroll_file.read()), skiprows=9)  # Ignorer les premières lignes
        except Exception as e:
            print("Erreur de lecture des fichiers Excel:", str(e))
            return jsonify({
                'error': 'Erreur de lecture des fichiers Excel. Vérifiez le format des fichiers.'
            }), 400

        # Afficher les colonnes pour déboguer
        print("Colonnes du fichier de pointage :", timesheet_df.columns.tolist())
        print("Colonnes du fichier de paie :", payroll_df.columns.tolist())

        # Vérifier si les colonnes AMO, CNSS et Date d'Embauche existent dans le journal de paie
        amo_col = next((col for col in payroll_df.columns if "AMO" in str(col).upper()), None)
        cnss_col = next((col for col in payroll_df.columns if "CNSS" in str(col).upper()), None)
        date_embauche_col = next(
            (col for col in payroll_df.columns 
             if "DATE" in str(col).upper() and "EMBAUCHE" in str(col).upper()), 
            None
        )

        # Nettoyer les données
        try:
            # Fichier de pointage
            timesheet_mapped = pd.DataFrame({
                'employeeId': timesheet_df['Matricule'].astype(str).str.strip(),
                'hoursWorked': pd.to_numeric(timesheet_df['HN/JN'], errors='coerce').fillna(0),
                'statusTimesheet': 'Present'  # Default to present
            })
            
            # Mark absent employees in timesheet (where hoursWorked is 0)
            timesheet_mapped.loc[timesheet_mapped['hoursWorked'] == 0, 'statusTimesheet'] = 'Employé absent dans pointage'

            # Fichier de journal de paie - Filtrer les lignes avec Matricule vide/NAN
            payroll_df = payroll_df.dropna(subset=['Matricule'])  # Remove rows with NaN Matricule
            payroll_df = payroll_df[payroll_df['Matricule'].astype(str).str.strip() != '']  # Remove empty Matricule
            payroll_df = payroll_df[~payroll_df['Matricule'].astype(str).str.upper().str.contains('NAN')]  # Remove 'NAN' values
            
            payroll_mapped = pd.DataFrame({
                'employeeId': payroll_df['Matricule'].astype(str).str.strip(),
                'employeeName': payroll_df['Nom et Prénom'].astype(str).str.strip(),
                'hoursPaid': pd.to_numeric(payroll_df['Jrs/Hrs'], errors='coerce').fillna(0),
                'statusPayroll': 'Present'  # Default to present
            })
            
            # Ajouter les colonnes de validation si elles existent
            if amo_col:
                payroll_mapped['amo'] = pd.to_numeric(payroll_df[amo_col], errors='coerce').fillna(0)
            
            if cnss_col:
                payroll_mapped['cnss'] = pd.to_numeric(payroll_df[cnss_col], errors='coerce').fillna(0)
                
            if date_embauche_col:
                # Convert to datetime and handle errors
                payroll_mapped['dateEmbauche'] = pd.to_datetime(
                    payroll_df[date_embauche_col], 
                    errors='coerce',
                    dayfirst=True  # Important for European date formats
                )
            
            # Mark absent employees in payroll (where hoursPaid is 0)
            payroll_mapped.loc[payroll_mapped['hoursPaid'] == 0, 'statusPayroll'] = 'Employé absent dans journal de paie'

        except KeyError as e:
            missing_column = str(e).strip("'")
            return jsonify({
                'error': f'Colonne manquante: {missing_column}'
            }), 400

        # Fusionner les DataFrames
        merged_df = pd.merge(
            timesheet_mapped,
            payroll_mapped,
            on='employeeId',
            how='outer',
            indicator=True
        )

        # Handle employees present in only one file
        merged_df.loc[merged_df['_merge'] == 'left_only', 'statusPayroll'] = 'Employé absent dans journal de paie'
        merged_df.loc[merged_df['_merge'] == 'right_only', 'statusTimesheet'] = 'Employé absent dans pointage'
        merged_df = merged_df.drop('_merge', axis=1)

        # Remplacer les valeurs NaN par 0 pour les calculs
        merged_df['hoursWorked'] = merged_df['hoursWorked'].fillna(0)
        merged_df['hoursPaid'] = merged_df['hoursPaid'].fillna(0)

        # Calculer la différence
        merged_df['difference'] = merged_df['hoursWorked'] - merged_df['hoursPaid']

        # Ajouter un champ pour indiquer les incohérences
        merged_df['hasIncoherence'] = (merged_df['difference'] != 0) | \
                                     (merged_df['statusTimesheet'] == 'Employé absent dans pointage') | \
                                     (merged_df['statusPayroll'] == 'Employé absent dans journal de paie')

        # Combine status information
        merged_df['status'] = merged_df.apply(lambda row: 
            f"{row['statusTimesheet']}, {row['statusPayroll']}" 
            if row['statusTimesheet'] != row['statusPayroll'] 
            else row['statusTimesheet'], 
            axis=1)

        # Filtrer les résultats finaux pour exclure les Matricules vides/NAN
        merged_df = merged_df[merged_df['employeeId'].astype(str).str.strip() != '']
        merged_df = merged_df[~merged_df['employeeId'].astype(str).str.upper().str.contains('NAN')]

        # Ajouter les validations de paie (AMO, CNSS, date d'embauche)
        def add_paie_validations(row):
            paie_validations = {}
            
            # AMO & CNSS Check
            amo_cnss_check = {"status": "Valid"}  # Default to Valid
            if 'amo' in row and 'cnss' in row:
                amo = float(row['amo']) if pd.notna(row['amo']) else 0
                cnss = float(row['cnss']) if pd.notna(row['cnss']) else 0
                
                amo_cnss_check = {
                    "amo": amo,
                    "cnss": cnss,
                    "status": "Valid" if amo > 0 and cnss > 0 else "Employé non déclaré"
                }
            paie_validations["amoCnssCheck"] = amo_cnss_check
            
            # Date d'Embauche Check with updated contract duration logic (matching port 8002)
            embauche_date_check = {"status": "Valid"}  # Default to Valid
            if 'dateEmbauche' in row:
                date_embauche = row['dateEmbauche']
                if pd.notna(date_embauche) and isinstance(date_embauche, pd.Timestamp):
                    today = pd.to_datetime('today')
                    anciennete_days = (today - date_embauche).days
                    anciennete_months = anciennete_days / 30  # Match port 8002 calculation
                    
                    embauche_date_check = {
                        "dateEmbauche": date_embauche.strftime('%Y-%m-%d'),  # Use ISO format
                        "anciennete": f"{anciennete_months:.1f} mois",
                        # Updated logic to match port 8002: "Fin de Contrat" if > 5 months
                        "status": "Fin de Contrat" if anciennete_months > 5 else "Valide"
                    }
                else:
                    embauche_date_check = {
                        "dateEmbauche": "Non spécifiée",
                        "anciennete": "Non calculée",
                        "status": "Non vérifié"
                    }
            paie_validations["embaucheDateCheck"] = embauche_date_check
            
            return paie_validations
        
        # Appliquer les validations de paie à chaque ligne
        merged_df['paieValidations'] = merged_df.apply(add_paie_validations, axis=1)

        # Convertir en liste de dictionnaires
        results = merged_df.to_dict('records')

        # Ajouter un résumé des résultats
        summary = {
            "total": len(results),
            "correct": sum(1 for r in results if not r["hasIncoherence"]),
            "inconsistencies": sum(1 for r in results if r["hasIncoherence"]),
            "employeesNotDeclared": sum(1 for r in results if 'paieValidations' in r and 
                                      r['paieValidations']['amoCnssCheck']['status'] == "Employé non déclaré"),
            "contractEnding": sum(1 for r in results if 'paieValidations' in r and 
                                r['paieValidations']['embaucheDateCheck']['status'] == "Fin de Contrat")
        }

        return jsonify({
            'status': 'success',
            'data': results,
            'summary': summary
        })

    except Exception as e:
        print(f"Erreur: {str(e)}")
        return jsonify({
            'error': f'Erreur lors du traitement des fichiers: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)