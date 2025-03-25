import React, { useState } from 'react';
import { AlertCircle, Upload, Loader2, ChevronLeft, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import ReactPaginate from 'react-paginate';
import Images from "../constant/images";

const Scif = () => {
  const [pointageFile, setPointageFile] = useState(null);
  const [paieFile, setPaieFile] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [rowsPerPage] = useState(10);
  const [statusFilter, setStatusFilter] = useState('all');

  // Filter results based on status
  const filteredResults = results?.results?.filter(item => 
    statusFilter === 'all' || item.status === statusFilter
  ) || [];

  // Pagination calculations
  const indexOfLastRow = (currentPage + 1) * rowsPerPage;
  const indexOfFirstRow = currentPage * rowsPerPage;
  const currentRows = filteredResults.slice(indexOfFirstRow, indexOfLastRow);
  const pageCount = Math.ceil(filteredResults.length / rowsPerPage);

  const handlePageClick = ({ selected }) => {
    setCurrentPage(selected);
  };

  const handleStatusFilterChange = (e) => {
    setStatusFilter(e.target.value);
    setCurrentPage(0);
  };

  const handlePointageChange = (e) => {
    setPointageFile(e.target.files[0]);
    setError(null);
    setResults(null);
    setCurrentPage(0);
  };

  const handlePaieChange = (e) => {
    setPaieFile(e.target.files[0]);
    setError(null);
    setResults(null);
    setCurrentPage(0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!pointageFile || !paieFile) {
      setError('Veuillez sélectionner les deux fichiers');
      return;
    }
    
    const validExtensions = ['.xlsx', '.xls'];
    const pointageExt = pointageFile.name.substring(pointageFile.name.lastIndexOf('.')).toLowerCase();
    const paieExt = paieFile.name.substring(paieFile.name.lastIndexOf('.')).toLowerCase();
    
    if (!validExtensions.includes(pointageExt) || !validExtensions.includes(paieExt)) {
      setError('Veuillez sélectionner des fichiers Excel (.xlsx ou .xls)');
      return;
    }
    
    setLoading(true);
    setError(null);
    setResults(null); 
    setCurrentPage(0);
    
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
        throw new Error(data.error || 'Une erreur est survenue lors du traitement des fichiers');
      }
      
      setResults(data);
    } catch (err) {
      setError(err.message || 'Erreur de connexion avec le serveur');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#1A1F2C] text-gray-100">
   <nav className="backdrop-blur-xl bg-black/40 border-b border-white/10 shadow-lg sticky top-0 z-10">
  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div className="flex items-center h-16">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <img src={Images.logo} alt="Logo" className="h-8 w-8" />
        </div>
        <div className="ml-4">
          <a href='/' className="text-xl font-bold text-white">SheetSync</a>
        </div>
      </div>

      <div className="hidden md:block ms-20">
        <ul className="flex space-x-4">
          <li className="relative group">
            <button className="text-gray-300 hover:text-[#efab1e] hover:bg-white/10 px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center">
              Traitement
              <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            <div className="absolute hidden group-hover:block bg-black/80 backdrop-blur-md border border-white/10 rounded-md shadow-lg min-w-[160px] z-20">
              <Link
                to="/scif"
                className="block px-4 py-2 text-sm text-gray-300 hover:text-[#efab1e] hover:bg-white/10 transition-colors"
              >
                SCIF
              </Link>
              <Link
                to="/novometal"
                className="block px-4 py-2 text-sm text-gray-300 hover:text-[#efab1e] hover:bg-white/10 transition-colors"
              >
                Novometal
              </Link>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</nav>

      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="bg-[#222222]/80 p-8 rounded-lg border border-gray-800 shadow-xl">
          <h1 className="text-2xl font-bold text-white mb-6">Traitement Pointage vs Paie</h1>
          
          <form onSubmit={handleSubmit} className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-300">
                  Fichier de Pointage (NORMAL)
                </label>
                <div className="flex items-center space-x-4">
                  <label className="flex flex-col items-center justify-center w-full h-36 border-2 border-gray-700 border-dashed rounded-lg cursor-pointer bg-[#333333] hover:bg-[#3A3A3A] transition-colors hover:border-gray-500 duration-200">
                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                      <Upload className="w-8 h-8 text-blue-400 mb-3" />
                      <p className="text-sm text-gray-400">
                        {pointageFile ? pointageFile.name : 'Cliquez pour sélectionner'}
                      </p>
                    </div>
                    <input 
                      type="file" 
                      accept=".xlsx, .xls" 
                      onChange={handlePointageChange}
                      className="hidden" 
                    />
                  </label>
                </div>
                <p className="text-xs text-gray-500 mt-1">Format attendu: CIN, Nom et Prénom, NORMAL</p>
              </div>
              
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-300">
                  Fichier de Journal de Paie (Jrs/Hrs)
                </label>
                <div className="flex items-center space-x-4">
                  <label className="flex flex-col items-center justify-center w-full h-36 border-2 border-gray-700 border-dashed rounded-lg cursor-pointer bg-[#333333] hover:bg-[#3A3A3A] transition-colors hover:border-gray-500 duration-200">
                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                      <Upload className="w-8 h-8 text-blue-400 mb-3" />
                      <p className="text-sm text-gray-400">
                        {paieFile ? paieFile.name : 'Cliquez pour sélectionner'}
                      </p>
                    </div>
                    <input 
                      type="file" 
                      accept=".xlsx, .xls" 
                      onChange={handlePaieChange}
                      className="hidden" 
                    />
                  </label>
                </div>
                <p className="text-xs text-gray-500 mt-1">Format attendu: CIN, Nom et Prénom, Jrs/Hrs</p>
              </div>
            </div>
            
            <div className="flex justify-center pt-4">
              <button 
                type="submit" 
                className="inline-flex items-center px-8 py-3 border border-transparent text-base font-medium rounded-md shadow-lg text-white bg-blue-950  focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                disabled={loading || !pointageFile || !paieFile}
              >
                {loading ? (
                  <>
                    <Loader2 className="animate-spin mr-3 h-5 w-5" />
                    Traitement en cours...
                  </>
                ) : 'Comparer les Fichiers'}
              </button>
            </div>
          </form>
          
          {error && (
            <div className="mt-8 p-4 bg-red-950/50 border-l-4 border-red-500 rounded-md backdrop-blur-sm">
              <div className="flex">
                <div className="flex-shrink-0">
                  <AlertCircle className="h-5 w-5 text-red-400" />
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-400">Erreur</h3>
                  <div className="mt-2 text-sm text-red-300">
                    <p>{error}</p>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {results && (
            <div className="mt-10 animate-fadeIn">
              <div className="mb-8 p-6 bg-gray-800/50 border border-gray-700 rounded-lg shadow-lg backdrop-blur-sm">
                <h2 className="text-lg font-semibold text-white mb-4">Résumé</h2>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 shadow-md transition-transform hover:scale-102 duration-200">
                    <p className="text-sm text-gray-400">Total employés</p>
                    <p className="text-2xl font-bold text-white">{results.summary.total}</p>
                  </div>
                  <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 shadow-md transition-transform hover:scale-102 duration-200">
                    <p className="text-sm text-gray-400">Correspondances</p>
                    <p className="text-2xl font-bold text-green-400">{results.summary.correct}</p>
                  </div>
                  <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 shadow-md transition-transform hover:scale-102 duration-200">
                    <p className="text-sm text-gray-400">Incohérences</p>
                    <p className="text-2xl font-bold text-red-400">{results.summary.inconsistencies}</p>
                  </div>
                </div>
              </div>

              {/* Status Filter */}
              <div className="mb-4 flex justify-end">
                <div className="w-full md:w-64">
                  <label htmlFor="statusFilter" className="block text-sm font-medium text-gray-300 mb-1">
                    Filtrer par statut
                  </label>
                  <select
                    id="statusFilter"
                    value={statusFilter}
                    onChange={handleStatusFilterChange}
                    className="w-full bg-gray-800 border border-gray-700 text-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">Tous les statuts</option>
                    <option value="Correct">Correct</option>
                    <option value="Incohérence">Incohérence</option>
                    <option value="Employé absent dans pointage">Employé absent dans pointage</option>
                    <option value="Employé absent dans journal de paie">Employé absent dans journal de paie</option>
                  </select>
                </div>
              </div>
              
              <div className="overflow-x-auto rounded-lg border border-gray-700 shadow-xl backdrop-blur-sm">
                <table className="min-w-full divide-y divide-gray-700">
                  <thead className="bg-gray-800">
                    <tr>
                      <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                       CIN
                      </th>
                      <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                       NORMAL (pointage)
                      </th>
                      <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Jrs/Hrs (Journal de paie)
                      </th>
                      <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Différence
                      </th>
                      <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Prime de Rendement
                      </th>
                      <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Statut
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-gray-900 divide-y divide-gray-800">
                    {currentRows.map((item, index) => (
                      <tr 
                        key={index} 
                        className={
                          item.status !== 'Correct' 
                            ? 'bg-yellow-900/20 hover:bg-yellow-900/30' 
                            : 'hover:bg-gray-800/50'
                        }
                        style={{ transition: 'background-color 0.2s ease' }}
                      >
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-200">
                          {item.CIN}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                          {item.heuresTravaillees.toFixed(2)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                          {item.heuresPayees.toFixed(2)}
                        </td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                          item.difference > 0 ? 'text-red-400' : 
                          item.difference < 0 ? 'text-red-800' : 'text-gray-400'
                        }`}>
                          {item.difference.toFixed(2)}
                        </td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                          item.primeRendement > 0 ? 'text-yellow-400' : 'text-gray-400'
                        }`}>
                          {item.primeRendement.toFixed(2)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            item.status === 'Correct' ? 'bg-green-900/50 text-green-400 border border-green-700' :
                            item.status === 'Employé absent dans journal de paie' ? 'bg-red-900/50 text-red-400 border border-red-700' :
                            'bg-red-900/50 text-red-400 border border-red-900'
                          }`}>
                            {item.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {/* Pagination */}
                <div className="flex items-center justify-between px-6 py-4 bg-gray-800 border-t border-gray-700">
                  <div className="text-sm text-gray-400">
                    Affichage {indexOfFirstRow + 1}-{Math.min(indexOfLastRow, filteredResults.length)} sur {filteredResults.length} résultats
                    {statusFilter !== 'all' && ` (Filtré: ${statusFilter})`}
                  </div>
                  <ReactPaginate
                    previousLabel={<ChevronLeft size={18} />}
                    nextLabel={<ChevronRight size={18} />}
                    breakLabel={<span className="text-gray-400">...</span>}
                    breakClassName="mx-1"
                    pageCount={pageCount}
                    marginPagesDisplayed={1}
                    pageRangeDisplayed={3}
                    onPageChange={handlePageClick}
                    containerClassName="flex items-center space-x-1"
                    pageClassName="flex"
                    pageLinkClassName="px-3 py-1 rounded-md text-sm text-gray-300 hover:bg-gray-700 transition-colors"
                    activeClassName="bg-blue-600 text-white"
                    activeLinkClassName="bg-blue-600 text-white hover:bg-blue-700"
                    previousClassName="p-1 rounded-md hover:bg-gray-700"
                    nextClassName="p-1 rounded-md hover:bg-gray-700"
                    disabledClassName="opacity-40 cursor-not-allowed"
                    disabledLinkClassName="cursor-not-allowed"
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Scif;