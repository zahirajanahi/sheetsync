from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from io import BytesIO

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
            timesheet_df = pd.read_excel(BytesIO(timesheet_file.read()))  # Fixed missing parenthesis

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

        # Convertir en liste de dictionnaires
        results = merged_df.to_dict('records')

        return jsonify({
            'status': 'success',
            'data': results
        })

    except Exception as e:
        print(f"Erreur: {str(e)}")
        return jsonify({
            'error': f'Erreur lors du traitement des fichiers: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)