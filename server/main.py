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
                'hoursWorked': pd.to_numeric(timesheet_df['HN/JN'], errors='coerce').fillna(0)
            })

            # Fichier de journal de paie
            payroll_mapped = pd.DataFrame({
                'employeeId': payroll_df['Matricule'].astype(str).str.strip(),
                'employeeName': payroll_df['Nom et Prénom'].astype(str).str.strip(),  # Utiliser le nom de la colonne
                'hoursPaid': pd.to_numeric(payroll_df['Jrs/Hrs'], errors='coerce').fillna(0)
            })
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
            how='outer'
        )

        # Remplacer les valeurs NaN par 0
        merged_df = merged_df.fillna(0)

        # Calculer la différence
        merged_df['difference'] = merged_df['hoursWorked'] - merged_df['hoursPaid']

        # Ajouter un champ pour indiquer les incohérences
        merged_df['hasIncoherence'] = merged_df['difference'] != 0

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