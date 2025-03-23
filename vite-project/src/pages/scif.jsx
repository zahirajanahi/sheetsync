import React, { useState } from 'react';
import { AlertCircle } from 'lucide-react';

const Scif = () => {
    const [pointageFile, setPointageFile] = useState(null);
  const [paieFile, setPaieFile] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handlePointageChange = (e) => {
    setPointageFile(e.target.files[0]);
  };

  const handlePaieChange = (e) => {
    setPaieFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!pointageFile || !paieFile) {
      setError('Veuillez sélectionner les deux fichiers');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    const formData = new FormData();
    formData.append('pointage', pointageFile);
    formData.append('paie', paieFile);
    
    try {
      const response = await fetch('http://localhost:8001/upload', {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Une erreur est survenue');
      }
      
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

    return (
        <div className="max-w-6xl mx-auto p-6 font-sans">
        <header className="bg-slate-800 text-white p-6 rounded-md mb-6 text-center">
          <h1 className="text-2xl font-bold">Comparaison des Heures Travaillées et Payées</h1>
        </header>
        
        <div className="bg-gray-50 p-6 rounded-md shadow-md">
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="flex flex-col">
              <label className="mb-2 font-semibold text-slate-700">Fichier de Pointage (Heures Travaillées)</label>
              <input 
                type="file" 
                accept=".xlsx, .xls" 
                onChange={handlePointageChange}
                className="p-3 border border-gray-300 rounded-md bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" 
              />
            </div>
            
            <div className="flex flex-col">
              <label className="mb-2 font-semibold text-slate-700">Fichier de Journal de Paie (Heures Payées)</label>
              <input 
                type="file" 
                accept=".xlsx, .xls" 
                onChange={handlePaieChange}
                className="p-3 border border-gray-300 rounded-md bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" 
              />
            </div>
            
            <button 
              type="submit" 
              className="md:col-span-2 bg-blue-500 hover:bg-blue-600 text-white py-3 px-4 rounded-md cursor-pointer text-lg transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
              disabled={loading}
            >
              {loading ? 'Traitement en cours...' : 'Comparer les Fichiers'}
            </button>
          </form>
          
          {error && (
            <div className="bg-red-100 text-red-800 p-4 rounded-md mb-6">
              Erreur: {error}
            </div>
          )}
          
          {results && (
            <div className="mt-8">
              <h2 className="text-xl font-bold text-slate-800 mb-4">Résultats de la Comparaison</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 bg-blue-50 p-4 rounded-md">
                <p>Total des employés: <span className="font-bold">{results.summary.total}</span></p>
                <p>Correct: <span className="font-bold">{results.summary.correct}</span></p>
                <p>Incohérences: <span className="font-bold">{results.summary.inconsistencies}</span></p>
              </div>
              
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr>
                      <th className="bg-slate-800 text-white p-3 text-left">Matricule</th>
                      <th className="bg-slate-800 text-white p-3 text-left">Heures Travaillées</th>
                      <th className="bg-slate-800 text-white p-3 text-left">Heures Payées (Jrs/Hrs)</th>
                      <th className="bg-slate-800 text-white p-3 text-left">Différence</th>
                      <th className="bg-slate-800 text-white p-3 text-left">Statut</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.results.map((item, index) => (
                      <tr 
                        key={index} 
                        className={
                          item.status !== 'Correct' 
                            ? 'bg-yellow-50 hover:bg-yellow-100' 
                            : (index % 2 === 0 ? 'bg-white hover:bg-blue-50' : 'bg-gray-50 hover:bg-blue-50')
                        }
                      >
                        <td className="p-3 border-b border-gray-200">{item.matricule}</td>
                        <td className="p-3 border-b border-gray-200">{item.heuresTravaillees.toFixed(2)}</td>
                        <td className="p-3 border-b border-gray-200">{item.heuresPayees.toFixed(2)}</td>
                        <td className={`p-3 border-b border-gray-200 ${item.difference !== 0 ? 'text-red-600 font-bold' : ''}`}>
                          {item.difference.toFixed(2)}
                        </td>
                        <td className="p-3 border-b border-gray-200">{item.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    );
};

export default Scif;