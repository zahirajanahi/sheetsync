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
            return jsonify({'error': 'Les deux fichiers sont requis'}), 400

        timesheet_file = request.files['timesheet']
        payroll_file = request.files['payroll']

        try:
            timesheet_df = pd.read_excel(BytesIO(timesheet_file.read()))
            payroll_df = pd.read_excel(BytesIO(payroll_file.read()), skiprows=9)
        except Exception as e:
            print("Erreur de lecture des fichiers Excel:", str(e))
            return jsonify({'error': 'Erreur de lecture des fichiers Excel. Vérifiez le format des fichiers.'}), 400

        print("Colonnes du fichier de pointage :", timesheet_df.columns.tolist())
        print("Colonnes du fichier de paie :", payroll_df.columns.tolist())

        if 'NCIN' not in timesheet_df.columns or 'NCIN' not in payroll_df.columns:
            return jsonify({'error': 'La colonne NCIN est requise dans les deux fichiers.'}), 400

        # Trouver la colonne "Total des heures"
        total_hours_col = next((col for col in timesheet_df.columns if "total" in col.lower() and "heure" in col.lower()), None)
        if not total_hours_col:
            return jsonify({'error': 'La colonne contenant "Total des heures" est introuvable dans le fichier de pointage.'}), 400

        # Trouver les colonnes nécessaires dans le journal de paie
        jrs_hrs_col = next((col for col in payroll_df.columns if "jrs" in col.lower() and "hrs" in col.lower()), None)
        if not jrs_hrs_col:
            return jsonify({'error': 'La colonne "Jrs/Hrs" est introuvable dans le journal de paie.'}), 400

        # Trouver les colonnes HS 25 et HS 50
        hs25_col = next((col for col in payroll_df.columns if "hs" in str(col).lower() and "25" in str(col)), None)
        hs50_col = next((col for col in payroll_df.columns if "hs" in str(col).lower() and "50" in str(col)), None)

        amo_col = next((col for col in payroll_df.columns if "AMO" in str(col).upper()), None)
        cnss_col = next((col for col in payroll_df.columns if "CNSS" in str(col).upper()), None)
        date_embauche_col = next((col for col in payroll_df.columns if "DATE" in str(col).upper() and "EMBAUCHE" in str(col).upper()), None)

        timesheet_mapped = pd.DataFrame({
            'employeeId': timesheet_df['NCIN'].astype(str).str.strip(),
            'hoursWorked': pd.to_numeric(timesheet_df[total_hours_col], errors='coerce').fillna(0),
            'statusTimesheet': 'Present'
        })
        timesheet_mapped.loc[timesheet_mapped['hoursWorked'] == 0, 'statusTimesheet'] = 'Employé absent dans pointage'

        payroll_df = payroll_df.dropna(subset=['NCIN'])
        payroll_df = payroll_df[payroll_df['NCIN'].astype(str).str.strip() != '']
        payroll_df = payroll_df[~payroll_df['NCIN'].astype(str).str.upper().str.contains('NAN')]

        # Calculate adjusted hours paid considering HS 25 and HS 50 columns if they exist
        payroll_df['adjusted_hours_paid'] = pd.to_numeric(payroll_df[jrs_hrs_col], errors='coerce').fillna(0)
        
        if hs25_col:
            hs25_hours = pd.to_numeric(payroll_df[hs25_col], errors='coerce').fillna(0)
            payroll_df['adjusted_hours_paid'] += hs25_hours * 1.25
        
        if hs50_col:
            hs50_hours = pd.to_numeric(payroll_df[hs50_col], errors='coerce').fillna(0)
            payroll_df['adjusted_hours_paid'] += hs50_hours * 1.50

        payroll_mapped = pd.DataFrame({
            'employeeId': payroll_df['NCIN'].astype(str).str.strip(),
            'employeeName': payroll_df['Nom et Prénom'].astype(str).str.strip(),
            'hoursPaid': payroll_df['adjusted_hours_paid'],
            'statusPayroll': 'Present'
        })

        if amo_col:
            payroll_mapped['amo'] = pd.to_numeric(payroll_df[amo_col], errors='coerce').fillna(0)
        if cnss_col:
            payroll_mapped['cnss'] = pd.to_numeric(payroll_df[cnss_col], errors='coerce').fillna(0)
        if date_embauche_col:
            payroll_mapped['dateEmbauche'] = pd.to_datetime(
                payroll_df[date_embauche_col], errors='coerce', dayfirst=True)

        payroll_mapped.loc[payroll_mapped['hoursPaid'] == 0, 'statusPayroll'] = 'Employé absent dans journal de paie'

        merged_df = pd.merge(timesheet_mapped, payroll_mapped, on='employeeId', how='outer', indicator=True)

        merged_df.loc[merged_df['_merge'] == 'left_only', 'statusPayroll'] = 'Employé absent dans journal de paie'
        merged_df.loc[merged_df['_merge'] == 'right_only', 'statusTimesheet'] = 'Employé absent dans pointage'
        merged_df = merged_df.drop('_merge', axis=1)

        merged_df['hoursWorked'] = merged_df['hoursWorked'].fillna(0)
        merged_df['hoursPaid'] = merged_df['hoursPaid'].fillna(0)

        merged_df['difference'] = merged_df['hoursWorked'] - merged_df['hoursPaid']

        merged_df['hasIncoherence'] = (
            (merged_df['difference'] != 0) |
            (merged_df['statusTimesheet'] == 'Employé absent dans pointage') |
            (merged_df['statusPayroll'] == 'Employé absent dans journal de paie')
        )

        merged_df['status'] = merged_df.apply(lambda row:
            f"{row['statusTimesheet']}, {row['statusPayroll']}" if row['statusTimesheet'] != row['statusPayroll']
            else row['statusTimesheet'], axis=1)

        merged_df = merged_df[merged_df['employeeId'].astype(str).str.strip() != '']
        merged_df = merged_df[~merged_df['employeeId'].astype(str).str.upper().str.contains('NAN')]

        def add_paie_validations(row):
            paie_validations = {}

            amo_cnss_check = {"status": "Valid"}
            if 'amo' in row and 'cnss' in row:
                amo = float(row['amo']) if pd.notna(row['amo']) else 0
                cnss = float(row['cnss']) if pd.notna(row['cnss']) else 0
                amo_cnss_check = {
                    "amo": amo,
                    "cnss": cnss,
                    "status": "Valid" if amo > 0 and cnss > 0 else "Employé non déclaré"
                }
            paie_validations["amoCnssCheck"] = amo_cnss_check

            embauche_date_check = {"status": "Valid"}
            if 'dateEmbauche' in row:
                date_embauche = row['dateEmbauche']
                if pd.notna(date_embauche) and isinstance(date_embauche, pd.Timestamp):
                    today = pd.to_datetime('today')
                    anciennete_days = (today - date_embauche).days
                    anciennete_months = anciennete_days / 30
                    embauche_date_check = {
                        "dateEmbauche": date_embauche.strftime('%Y-%m-%d'),
                        "anciennete": f"{anciennete_months:.1f} mois",
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

        merged_df['paieValidations'] = merged_df.apply(add_paie_validations, axis=1)

        results = merged_df.to_dict('records')

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
        return jsonify({'error': f'Erreur lors du traitement des fichiers: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8004)