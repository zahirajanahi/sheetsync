import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertCircle, Upload, Loader2 } from 'lucide-react';
import axios from 'axios';
import { Images } from "../constant";

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!files.timesheet || !files.payroll) {
      setError('Veuillez sélectionner les deux fichiers');
      return;
    }

    setLoading(true);
    setError('');
    setIncoherenceAlert('');
    setResults([]);

    const formData = new FormData();
    formData.append('timesheet', files.timesheet);
    formData.append('payroll', files.payroll);

    try {
      const response = await axios.post('http://localhost:8000/api/compare', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (response.data.status === 'success') {
        setResults(response.data.data);

        // Check for inconsistencies
        const incoherences = response.data.data.filter((result) => result.hasIncoherence);
        if (incoherences.length > 0) {
          const alertMessage = incoherences
            .map((result) => `Matricule: ${result.employeeId}, Nom: ${result.employeeName}, Différence: ${result.difference.toFixed(2)}`)
            .join('\n');
          setIncoherenceAlert(`Incohérences détectées :\n${alertMessage}`);
        } else {
          setIncoherenceAlert('Aucune incohérence détectée. Tout est en ordre !');
        }
      } else {
        setError('Erreur lors de la comparaison des données');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Erreur lors de la communication avec le serveur');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#1A1F2C] text-gray-100">
      {/* Glass morphism navbar */}
      <nav className="backdrop-blur-xl bg-black/40 border-b border-white/10 shadow-lg sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <img
                  className="h-8 w-8"
                  src={Images.logo}
                  alt="Logo"
                />
              </div>
              <div className="ml-4">
              <a href='/' className="text-xl font-bold text-white">SheetSync</a>
              </div>
            </div>
      
            <div className="hidden md:block ms-20">
              <ul className="flex space-x-4">
                <li>
                  <Link
                    to="/scif"
                    className="text-gray-300 hover:text-[#efab1e] hover:bg-white/10 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                  >
                    SCIF
                  </Link>
                </li>
                <li>
                  <Link
                    to="/novometal"
                    className="text-gray-300 hover:text-[#efab1e] hover:bg-white/10 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                  >
                    Novometal
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="bg-[#222222]/80 backdrop-blur-lg border border-white/10 p-6 rounded-lg shadow-lg transition-all duration-300 hover:shadow-xl animate-fadeIn">
          <h1 className="text-2xl font-bold text-white mb-6">Comparaison Pointage vs Paie</h1>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-300">
                  Fichier de Pointage (HN/JN)
                </label>
                <div className="flex items-center space-x-4">
                  <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-700 border-dashed rounded-lg cursor-pointer bg-[#333333] hover:bg-[#3A3A3A] transition-colors hover:border-gray-500">
                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                      <Upload className="w-8 h-8 text-gray-400 mb-2" />
                      <p className="text-sm text-gray-400">
                        {files.timesheet ? files.timesheet.name : 'Cliquez pour sélectionner'}
                      </p>
                    </div>
                    <input 
                      type="file" 
                      name="timesheet"
                      accept=".xlsx, .xls" 
                      onChange={handleFileChange}
                      className="hidden" 
                    />
                  </label>
                </div>
                <p className="text-xs text-gray-400 mt-1">Format attendu: Matricule, Nom et Prénom, HN/JN</p>
              </div>
              
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-300">
                  Fichier de Journal de Paie (Jrs/Hrs)
                </label>
                <div className="flex items-center space-x-4">
                  <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-700 border-dashed rounded-lg cursor-pointer bg-[#333333] hover:bg-[#3A3A3A] transition-colors hover:border-gray-500">
                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                      <Upload className="w-8 h-8 text-gray-400 mb-2" />
                      <p className="text-sm text-gray-400">
                        {files.payroll ? files.payroll.name : 'Cliquez pour sélectionner'}
                      </p>
                    </div>
                    <input 
                      type="file" 
                      name="payroll"
                      accept=".xlsx, .xls" 
                      onChange={handleFileChange}
                      className="hidden" 
                    />
                  </label>
                </div>
                <p className="text-xs text-gray-400 mt-1">Format attendu: Matricule, Nom et Prénom, Jrs/Hrs</p>
              </div>
            </div>
            
            <div className="flex justify-center">
              <button 
                type="submit" 
                className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-950 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors hover:scale-102"
                disabled={loading || !files.timesheet || !files.payroll}
              >
                {loading ? (
                  <>
                    <Loader2 className="animate-spin mr-2 h-5 w-5" />
                    Traitement en cours...
                  </>
                ) : 'Comparer les Fichiers'}
              </button>
            </div>
          </form>
          
          {error && (
            <div className="mt-6 p-4 bg-red-900/30 border-l-4 border-red-500 rounded-md backdrop-blur-lg">
              <div className="flex">
                <div className="flex-shrink-0">
                  <AlertCircle className="h-5 w-5 text-red-400" />
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-300">Erreur</h3>
                  <div className="mt-2 text-sm text-red-200">
                    <p>{error}</p>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {incoherenceAlert && (
            <div className={`mt-6 p-4 border-l-4 rounded-md backdrop-blur-lg ${
              incoherenceAlert.includes('Aucune incohérence') 
                ? 'bg-green-900/30 border-green-500' 
                : 'bg-yellow-900/30 border-yellow-500'
            }`}>
              <div className="flex">
                <div className="flex-shrink-0">
                  <AlertCircle className={`h-5 w-5 ${
                    incoherenceAlert.includes('Aucune incohérence') 
                      ? 'text-green-400' 
                      : 'text-yellow-400'
                  }`} />
                </div>
                <div className="ml-3">
                  <h3 className={`text-sm font-medium ${
                    incoherenceAlert.includes('Aucune incohérence') 
                      ? 'text-green-300' 
                      : 'text-yellow-300'
                  }`}>
                    {incoherenceAlert.includes('Aucune incohérence') 
                      ? 'Succès' 
                      : 'Avertissement'}
                  </h3>
                  <div className={`mt-2 text-sm ${
                    incoherenceAlert.includes('Aucune incohérence') 
                      ? 'text-green-200' 
                      : 'text-yellow-200'
                  }`}>
                    <p className="whitespace-pre-line">{incoherenceAlert}</p>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {results.length > 0 && (
            <div className="mt-8">
              <div className="overflow-x-auto shadow-md rounded-lg">
                <table className="min-w-full divide-y divide-gray-700">
                  <thead className="bg-gray-800">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Matricule
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Nom et Prénom
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        HN/JN (pointage)
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Jrs/Hrs (paie)
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Différence
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {results.map((result, index) => (
                      <tr 
                        key={index} 
                        className={result.hasIncoherence ? 'bg-red-900/20 hover:bg-red-900/30' : 'bg-[#2A2A2A] hover:bg-[#333333]'}
                      >
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-200">
                          {result.employeeId}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                          {result.employeeName}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                          {result.hoursWorked.toFixed(2)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                          {result.hoursPaid.toFixed(2)}
                        </td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                          result.difference > 0 ? 'text-red-400' : 
                          result.difference < 0 ? 'text-red-400' : 'text-green-400'
                        }`}>
                          {result.difference.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Novometal;