import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertCircle, Upload, Loader2, ChevronLeft, ChevronRight } from 'lucide-react';
import axios from 'axios';
import ReactPaginate from 'react-paginate';
import { Images } from "../constant";

const Novometal = () => {
  const [files, setFiles] = useState({ timesheet: null, payroll: null });
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const [rowsPerPage] = useState(10);
  const [statusFilter, setStatusFilter] = useState('all');
  const [matriculeFilter, setMatriculeFilter] = useState('');

  // Filter results based on status and matricule
  const filteredResults = results.filter(result => 
    (statusFilter === 'all' || 
    (statusFilter === 'Correct' && !result.hasIncoherence) ||
    (statusFilter === 'Incohérence' && result.hasIncoherence)) &&
    (matriculeFilter === '' || 
     result.employeeId.toLowerCase().includes(matriculeFilter.toLowerCase()))
  );

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

  const handleMatriculeFilterChange = (e) => {
    setMatriculeFilter(e.target.value);
    setCurrentPage(0);
  };

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
    setResults([]);
    setCurrentPage(0);

    const formData = new FormData();
    formData.append('timesheet', files.timesheet);
    formData.append('payroll', files.payroll);

    try {
      const response = await axios.post('http://localhost:8000/api/compare', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (response.data.status === 'success') {
        setResults(response.data.data);
      } else {
        setError('Erreur lors de la comparaison des données');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Erreur lors de la communication avec le serveur');
    } finally {
      setLoading(false);
    }
  };

  // Calculate summary statistics
  const summary = {
    total: results.length,
    correct: results.filter(result => !result.hasIncoherence).length,
    inconsistencies: results.filter(result => result.hasIncoherence).length,
    totalDifference: results.reduce((sum, result) => sum + Math.abs(result.difference), 0)
  };

  // Function to determine status text and color
  const getStatusInfo = (result) => {
    if (!result.hasIncoherence) {
      return { text: 'Correct', color: 'green' };
    }
    
    if (result.statusTimesheet === 'Employé absent dans pointage' && 
        result.statusPayroll === 'Employé absent dans journal de paie') {
      return { text: 'Absent dans les deux', color: 'red' };
    }
    
    if (result.statusTimesheet === 'Employé absent dans pointage') {
      return { text: 'Absent dans pointage', color: 'red' };
    }
    
    if (result.statusPayroll === 'Employé absent dans journal de paie') {
      return { text: 'Absent dans paie', color: 'red' };
    }
    
    if (result.difference !== 0) {
      return { text: 'Incohérence heures', color: 'red' };
    }
    
    return { text: 'Inconnu', color: 'gray' };
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
                  <button className="text-gray-300 hover:text-[#5c67cb] hover:bg-white/10 px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center">
                    Traitement
                    <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  <div className="absolute hidden group-hover:block bg-black backdrop-blur-md border border-white/10 rounded-md shadow-lg min-w-[160px] z-20">
                    <Link to="/scif" className="block px-4 py-2 text-sm text-gray-300 hover:text-[#5c67cb] hover:bg-white/10 transition-colors">
                      SCIF
                    </Link>
                    <Link to="/novometal" className="block px-4 py-2 text-sm text-gray-300 hover:text-[#5c67cb] hover:bg-white/10 transition-colors">
                      Novometal
                    </Link>
                    <Link to="/afric-ph" className="block px-4 py-2 text-sm text-gray-300 hover:text-[#5c67cb] hover:bg-white/10 transition-colors">
                      Afric-ph 
                   </Link>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="bg-[#222222]/80 backdrop-blur-lg border border-white/10 p-6 rounded-lg shadow-lg transition-all duration-300 hover:shadow-xl animate-fadeIn">
          <h1 className="text-2xl font-bold text-white mb-6">Traitement Pointage vs Paie Novometal</h1>
          
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
          
          {results.length > 0 && (
            <div className="mt-8">
              {/* Summary Cards */}
              <div className="mb-8 p-6 bg-gray-800/50 border border-gray-700 rounded-lg shadow-lg backdrop-blur-sm">
                <h2 className="text-lg font-semibold text-white mb-4">Résumé</h2>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 shadow-md transition-transform hover:scale-102 duration-200">
                    <p className="text-sm text-gray-400">Total employés</p>
                    <p className="text-2xl font-bold text-white">{summary.total}</p>
                  </div>
                  <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 shadow-md transition-transform hover:scale-102 duration-200">
                    <p className="text-sm text-gray-400">Correspondances</p>
                    <p className="text-2xl font-bold text-green-400">{summary.correct}</p>
                  </div>
                  <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 shadow-md transition-transform hover:scale-102 duration-200">
                    <p className="text-sm text-gray-400">Incohérences</p>
                    <p className="text-2xl font-bold text-red-400">{summary.inconsistencies}</p>
                  </div>
                </div>
              </div>

              {/* Combined Filters */}
              <div className="mb-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="matriculeFilter" className="block text-sm font-medium text-gray-300 mb-1">
                    Filtrer par Matricule
                  </label>
                  <input
                    type="text"
                    id="matriculeFilter"
                    value={matriculeFilter}
                    onChange={handleMatriculeFilterChange}
                    placeholder="Rechercher par Matricule..."
                    className="w-full bg-gray-800 border border-gray-700 text-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
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
                  </select>
                </div>
              </div>

              {/* Results Table */}
              <div className="overflow-x-auto rounded-lg border border-gray-700 shadow-xl backdrop-blur-sm">
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
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Statut
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {currentRows.map((result, index) => {
                      const statusInfo = getStatusInfo(result);
                      return (
                        <tr 
                          key={index} 
                          className={result.hasIncoherence ? 'bg-yellow-900/20 hover:bg-yellow-900/30' : 'hover:bg-gray-800/50'}
                        >
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-200">
                            {result.employeeId}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                            {result.employeeName || 'N/A'}
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
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              statusInfo.color === 'green' 
                                ? 'bg-green-900/50 text-green-400 border border-green-700' 
                                : 'bg-red-900/50 text-red-400 border border-red-700'
                            }`}>
                              {statusInfo.text}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>

                {/* Pagination */}
                <div className="flex items-center justify-between px-6 py-4 bg-gray-800 border-t border-gray-700">
                  <div className="text-sm text-gray-400">
                    Affichage {indexOfFirstRow + 1}-{Math.min(indexOfLastRow, filteredResults.length)} sur {filteredResults.length} résultats
                    {(statusFilter !== 'all' || matriculeFilter !== '') && (
                      <span> (Filtré: {statusFilter !== 'all' ? `${statusFilter}` : ''}
                      {statusFilter !== 'all' && matriculeFilter !== '' ? ' et ' : ''}
                      {matriculeFilter !== '' ? `Matricule contenant "${matriculeFilter}"` : ''})</span>
                    )}
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

export default Novometal;