import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertCircle } from 'lucide-react';
import axios from 'axios';

const Novometal = () => {
    const [files, setFiles] = useState({ timesheet: null, payroll: null });
    const [results, setResults] = useState([]);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [incoherenceAlert, setIncoherenceAlert] = useState('');
  
    const handleFileChange = (e) => {
      const { name, files: fileList } = e.target;
      if (fileList && fileList[0]) {
        setFiles((prev) => ({ ...prev, [name]: fileList[0] }));
        setError('');
      }
    };
  
    const handleSubmit = async () => {
      if (!files.timesheet || !files.payroll) {
        setError('Veuillez sélectionner les deux fichiers.');
        return;
      }
  
      setLoading(true);
      setError('');
      setIncoherenceAlert('');
  
      const formData = new FormData();
      formData.append('timesheet', files.timesheet);
      formData.append('payroll', files.payroll);
  
      try {
        const response = await axios.post('http://localhost:8000/api/compare', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
  
        if (response.data.status === 'success') {
          setResults(response.data.data);
  
          // Vérifier les incohérences
          const incoherences = response.data.data.filter((result) => result.hasIncoherence);
          if (incoherences.length > 0) {
            const alertMessage = incoherences
              .map((result) => `Matricule: ${result.employeeId}, Nom: ${result.employeeName}, Différence: ${result.difference.toFixed(2)}`)
              .join('\n');
            setIncoherenceAlert(`Incohérences détectées :\n${alertMessage}`);
          } else {
            // Aucune incohérence détectée
            setIncoherenceAlert('Aucune incohérence détectée. Tout est en ordre !');
          }
        } else {
          setError('Erreur lors de la comparaison des données.');
        }
      } catch (err) {
        setError(err.response?.data?.error || 'Erreur lors de la communication avec le serveur.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
  
    return (
      <div className="min-h-screen bg-gray-100">
        {/* Navbar */}
        <nav className="bg-white shadow-md">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex items-center  h-16">
        {/* Logo and Title */}
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <img
              className="h-8 w-8"
              src="https://via.placeholder.com/50"
              alt="Logo"
            />
          </div>
          <div className="ml-4">
            <h1 className="text-xl font-bold text-gray-900">SheetSync</h1>
          </div>
        </div>
  
        {/* Navigation Links */}
        <div className="hidden md:block ms-20">
          <ul className="flex space-x-4">
            <li>
            <Link
                to="/scif"
                className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
              >
                SCIF
              </Link>
            </li>
            <li>
              <Link
                to="/novometal"
                className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
              >
                Novometal
              </Link>
            </li>
          
          </ul>
        </div>
      </div>
    </div>
  </nav>
  
        {/* Main Content */}
        <div className="py-8 px-4">
          <div className="max-w-7xl mx-auto">
            {error && (
              <div className="mb-4 p-4 bg-red-100 border border-red-400 rounded flex items-center">
                <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                <span className="text-red-700">{error}</span>
              </div>
            )}
  
            {incoherenceAlert && (
              <div
                className={`mb-4 p-4 border rounded flex items-center ${
                  incoherenceAlert.includes('Aucune incohérence')
                    ? 'bg-green-100 border-green-400'
                    : 'bg-yellow-100 border-yellow-400'
                }`}
              >
                <AlertCircle
                  className={`w-5 h-5 mr-2 ${
                    incoherenceAlert.includes('Aucune incohérence')
                      ? 'text-green-500'
                      : 'text-yellow-500'
                  }`}
                />
                <span
                  className={`whitespace-pre-line ${
                    incoherenceAlert.includes('Aucune incohérence')
                      ? 'text-green-700'
                      : 'text-yellow-700'
                  }`}
                >
                  {incoherenceAlert}
                </span>
              </div>
            )}
  
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
              <div className="space-y-2">
                <label className="block text-gray-700 text-sm font-medium mb-2">Fichier de pointage (Excel)</label>
                <input type="file" name="timesheet" accept=".xlsx,.xls" onChange={handleFileChange} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500" />
                <p className="text-sm text-gray-500">Format attendu: Matricule, Nom et Prénom, HN/JN</p>
              </div>
  
              <div className="space-y-2">
                <label className="block text-gray-700 text-sm font-medium mb-2">Fichier de paie (Excel)</label>
                <input type="file" name="payroll" accept=".xlsx,.xls" onChange={handleFileChange} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500" />
                <p className="text-sm text-gray-500">Format attendu: Matricule, Nom et Prénom, Jrs/Hrs</p>
              </div>
            </div>
  
            <div className="text-center mb-8">
              <button
                onClick={handleSubmit}
                disabled={!files.timesheet || !files.payroll || loading}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Comparaison en cours...' : 'Comparer les données'}
              </button>
            </div>
  
            {results.length > 0 && (
              <div className="overflow-x-auto">
                <table className="min-w-full bg-white border border-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Matricule</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nom et Prénom</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">HN/JN <br /> (pointage)</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Jrs/Hrs <br /> (journal de paie)</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Différence</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {results.map((result, index) => (
                      <tr key={index} className={result.hasIncoherence ? 'bg-red-50' : ''}>
                        <td className="px-6 py-4 whitespace-nowrap">{result.employeeId}</td>
                        <td className="px-6 py-4 whitespace-nowrap">{result.employeeName}</td>
                        <td className="px-6 py-4 whitespace-nowrap">{result.hoursWorked.toFixed(2)}</td>
                        <td className="px-6 py-4 whitespace-nowrap">{result.hoursPaid.toFixed(2)}</td>
                        <td
                          className="px-6 py-4 whitespace-nowrap font-medium"
                          style={{ color: result.difference > 0 ? 'red' : result.difference < 0 ? 'red' : 'green' }}
                        >
                          {result.difference.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

export default Novometal;