//code 1
import React, { useState } from 'react';
import { AlertCircle, Upload, Loader2, ChevronLeft, ChevronRight, Info, Check, X } from 'lucide-react';
import { Link } from 'react-router-dom';
import ReactPaginate from 'react-paginate';
import Images from "../constant/images";
import {  useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LogOut } from 'lucide-react';


const Cobco = () => {
  const [pointageFile, setPointageFile] = useState(null);
  const [paieFile, setPaieFile] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [rowsPerPage] = useState(10);
  const [statusFilter, setStatusFilter] = useState('all');
  const [cinFilter, setCinFilter] = useState('');
  const [incoherenceTypeFilter, setIncoherenceTypeFilter] = useState('all');
  const [expandedRows, setExpandedRows] = useState([]);

   const { user, signOut } = useAuth();
    const navigate = useNavigate();
  
    const handleLogout = async () => {
      await signOut();
      navigate('/');
    };
  
    if (!user) return null;
  

  // Filter results based on status, CIN, and incoherence type
  const filteredResults = results?.results?.filter(item => {

    // Status filter
    const statusMatch = statusFilter === 'all' || 
                   item.status === statusFilter ||
                   (statusFilter === 'Fin de Contrat' && 
                    item.paieValidations?.embaucheDateCheck?.status === 'Fin de Contrat') ||
                   (statusFilter === 'Employé non déclaré' && 
                    item.paieValidations?.amoCnssCheck?.status === 'Employé non déclaré');
    
    // CIN filter
    const cinMatch = cinFilter === '' || 
      (item.CIN && item.CIN.toLowerCase().includes(cinFilter.toLowerCase()));
    
    // Incoherence type filter
   
let incoherenceMatch = true;
if (incoherenceTypeFilter !== 'all' && statusFilter !== 'Correct') {
  switch(incoherenceTypeFilter) {
    case 'hs25':
      incoherenceMatch = item.hs25Status === 'Incohérence';
      break;
    case 'hs50':
      incoherenceMatch = item.hs50Status === 'Incohérence';
      break;
    case 'heures':
      incoherenceMatch = Math.abs(item.difference) > 0.01;
      break;
    default:
      incoherenceMatch = true;
  }
}
    
    return statusMatch && cinMatch && incoherenceMatch;
  }) || [];

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

  const handleIncoherenceTypeFilterChange = (e) => {
    setIncoherenceTypeFilter(e.target.value);
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

  const toggleRowExpand = (cin) => {
    setExpandedRows(prev => 
      prev.includes(cin) 
        ? prev.filter(item => item !== cin) 
        : [...prev, cin]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Reset states
    setError(null);
    setResults(null);
    setCurrentPage(0);
    setExpandedRows([]);
    
    if (!pointageFile || !paieFile) {
      setError('Veuillez sélectionner les deux fichiers');
      return;
    }
    
    // File validation
    const validExtensions = ['.xlsx', '.xls', '.csv'];
    const pointageExt = pointageFile.name.substring(pointageFile.name.lastIndexOf('.')).toLowerCase();
    const paieExt = paieFile.name.substring(paieFile.name.lastIndexOf('.')).toLowerCase();
    
    if (!validExtensions.includes(pointageExt) || !validExtensions.includes(paieExt)) {
      setError('Veuillez sélectionner des fichiers Excel (.xlsx, .xls) ou CSV');
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await fetch('http://localhost:8002/upload', {
        method: 'POST',
        body: createFormData(),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Erreur serveur');
      }
      
      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message || 'Erreur de connexion avec le serveur');
      console.error('API Error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Helper function to create form data
  const createFormData = () => {
    const formData = new FormData();
    formData.append('pointage', pointageFile);
    formData.append('paie', paieFile);
    return formData;
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'Correct':
        return 'bg-green-900/50 text-green-400 border border-green-700';
      case 'Employé absent dans pointage':
        return 'bg-purple-900/50 text-purple-400 border border-purple-700';
      case 'Employé absent dans journal de paie':
        return 'bg-orange-900/50 text-orange-400 border border-orange-700';
      case 'Fin de Contrat':
        return 'bg-blue-900/50 text-blue-400 border border-blue-700';
      case 'Employé non déclaré':
        return 'bg-red-900/50 text-red-400 border border-red-700';
      default:
        return 'bg-red-900/50 text-red-400 border border-red-700';
    }
  };

  return (
    <div className="min-h-screen bg-[#1A1F2C] text-gray-100">
   <nav className="backdrop-blur-xl bg-black/40 border-b border-white/10 shadow-lg sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <img src={Images.logo} alt="Logo" className="h-8 w-8" />
              </div>
              <div className="ml-4">
                <Link to="/" className="text-xl font-bold text-white">SheetSync</Link>
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
                      <Link to="/cobco" className="block px-4 py-2 text-sm text-gray-300 hover:text-[#5c67cb] hover:bg-white/10 transition-colors">
                        COBCO
                      </Link>
                      <Link to="/casaEaro" className="block px-4 py-2 text-sm text-gray-300 hover:text-[#5c67cb] hover:bg-white/10 transition-colors">
                        CasaEaro
                      </Link>
                      <Link to="/sbbc" className="block px-4 py-2 text-sm text-gray-300 hover:text-[#5c67cb] hover:bg-white/10 transition-colors">
                        SBBC
                      </Link>
                      <Link to="/other" className="block px-4 py-2 text-sm text-gray-300 hover:text-[#5c67cb] hover:bg-white/10 transition-colors">
                        Grand Ceram
                      </Link>
                    </div>
                  </li>
                   
                  <li  className='"text-gray-500 hover:text-[#5c67cb] hover:bg-white/10 px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-cente'>
                    <Link to="/temp"> Template </Link>
                  </li>

                  <li  className='"text-gray-500 hover:text-[#5c67cb] hover:bg-white/10 px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-cente'>
                    <Link to="/temp2"> Template 2 </Link>
                  </li>

                </ul>
              </div>
            </div>
            <div className="flex items-center">
              <button
                onClick={handleLogout}
                className="flex items-center px-4 py-2 text-sm font-medium px-3 py-1 bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-full text-xs"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Déconnexion
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="bg-[#222222]/80 p-8 rounded-lg border border-gray-800 shadow-xl">
          <h1 className="text-2xl font-bold text-white mb-6">Traitement Pointage vs Paie COBCO</h1>
          
          <form onSubmit={handleSubmit} className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-300">
                  Fichier de Pointage (JRS/HRS)
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
                      accept=".xlsx, .xls, .csv" 
                      onChange={handlePointageChange}
                      className="hidden" 
                    />
                  </label>
                </div>
                <p className="text-xs text-gray-500 mt-1">Format attendu: NCIN, Jrs/Hrs, HS 25</p>
              </div>
              
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-300">
                  Fichier de Journal de Paie (JRS/HRS)
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
                      accept=".xlsx, .xls, .csv" 
                      onChange={handlePaieChange}
                      className="hidden" 
                    />
                  </label>
                </div>
                <p className="text-xs text-gray-500 mt-1">Format attendu: NCIN, Jrs/Hrs, HS 25</p>
              </div>
            </div>
            
            <div className="flex justify-center pt-4">
              <button 
                type="submit" 
                className="inline-flex items-center px-8 py-3 border border-transparent text-base font-medium rounded-md shadow-lg text-white bg-blue-950 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
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
    
    {/* New: Validation Summary */}
  
  
    
    <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 shadow-md transition-transform hover:scale-102 duration-200">
      <p className="text-sm text-gray-400">Fin de contrat</p>
      <p className="text-2xl font-bold text-blue-400">
        {results.results.filter(r => 
          r.paieValidations?.embaucheDateCheck?.status === 'Fin de Contrat').length}
      </p>
    </div>
    
    <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 shadow-md transition-transform hover:scale-102 duration-200">
      <p className="text-sm text-gray-400">Employee Non déclarés</p>
      <p className="text-2xl font-bold text-red-400">
        {results.results.filter(r => 
          r.paieValidations?.amoCnssCheck?.status === 'Employé non déclaré').length}
      </p>
    </div>
  </div>
</div>

              {/* Combined Filters */}
              <div className="mb-4 flex flex-col md:flex-row gap-4">
                <div className="w-full md:w-64">
                  <label htmlFor="cinFilter" className="block text-sm font-medium text-gray-300 mb-1">
                    Filtrer par CIN
                  </label>
                  <input
                    type="text"
                    id="cinFilter"
                    value={cinFilter}
                    onChange={(e) => {
                      setCinFilter(e.target.value);
                      setCurrentPage(0);
                    }}
                    placeholder="Rechercher par CIN..."
                    className="w-full bg-gray-800 border border-gray-700 text-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
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
  <option value="Fin de Contrat">Fin de Contrat</option>
  <option value="Employé non déclaré">Employé non déclaré</option>
</select>

                </div>

                {statusFilter !== 'Correct' && (
                  <div className="w-full md:w-64">
                    <label htmlFor="incoherenceTypeFilter" className="block text-sm font-medium text-gray-300 mb-1">
                      Filtrer par type d'incohérence
                    </label>
                    <select
  id="incoherenceTypeFilter"
  value={incoherenceTypeFilter}
  onChange={handleIncoherenceTypeFilterChange}
  className="w-full bg-gray-800 border border-gray-700 text-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
>
  <option value="all">Tous les types</option>
  <option value="hs25">Incohérences HS 25</option>
  <option value="hs50">Incohérences HS 50</option>
  <option value="heures">Incohérences Heures</option>
</select>
                  </div>
                )}
              </div>
              
              <div className="overflow-x-auto rounded-lg border border-gray-700 shadow-xl backdrop-blur-sm">
                <table className="min-w-full divide-y divide-gray-700">
                  <thead className="bg-gray-800">
                    <tr>
                      <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        CIN
                      </th>
                      <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-300 tracking-wider">
                        Jrs/Hrs <br /> (Pointage)
                      </th>
                      <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-300 tracking-wider">
                      Jrs/Hrs <br /> (Paie)
                      </th>
                      <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Différence
                      </th>
                      <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Prime Rendement
                      </th>
                      <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Statut
                      </th>
                      <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-gray-900 divide-y divide-gray-800">
                    {currentRows.map((item, index) => (
                      <>
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
                            {item.heuresTravaillees?.toFixed(2) || '0.00'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                            {item.heuresPayees?.toFixed(2) || '0.00'}
                          </td>
                          <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                            item.difference > 0 ? 'text-red-400' : 
                            item.difference < 0 ? 'text-red-800' : 'text-gray-400'
                          }`}>
                            {item.difference?.toFixed(2) || '0.00'}
                          </td>
                          <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                            item.primeRendement > 0 ? 'text-yellow-400' : 'text-gray-400'
                          }`}>
                            {item.primeRendement?.toFixed(2) || '0.00'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadge(item.status)}`}>
                              {item.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <button 
                              onClick={() => toggleRowExpand(item.CIN)}
                              className="text-blue-400 hover:text-blue-300"
                            >
                              {expandedRows.includes(item.CIN) ? 'Masquer détails' : 'Voir détails'}
                            </button>
                          </td>
                        </tr>

                        {expandedRows.includes(item.CIN) && (

  <tr className="bg-gray-800/50">
    <td colSpan="7" className="px-6 py-4">
      <div className="space-y-3">
      {/* <div className={`p-3 rounded-lg ${
          item.paieValidations?.acompteNetCheck?.status === 'Valid' 
            ? 'bg-green-900/20' 
            : 'bg-yellow-900/20'
        }`}>
          <div className="flex items-center">
            {item.paieValidations?.acompteNetCheck?.status === 'Valid' ? (
              <Check className="w-4 h-4 text-green-400 mr-2" />
            ) : (
              <AlertCircle className="w-4 h-4 text-yellow-400 mr-2" />
            )}
            <span className="font-medium text-sm">
              Validation Acompte + Net Payé: 
            </span>
            <span className={`ml-2 text-sm ${
              item.paieValidations?.acompteNetCheck?.status === 'Valid' 
                ? 'text-green-400' 
                : 'text-yellow-400'
            }`}>
              {item.paieValidations?.acompteNetCheck?.status || 'Non vérifié'}
            </span>
          </div>
          {item.paieValidations?.acompteNetCheck && (
            <>
              <div className="mt-1 text-xs text-gray-300">
                Acompte: {item.paieValidations.acompteNetCheck.acompte?.toFixed(2) || '0.00'}
              </div>
              <div className="mt-1 text-xs text-gray-300">
                Net Payé: {item.paieValidations.acompteNetCheck.netPaye?.toFixed(2) || '0.00'}
              </div>
              <div className="mt-1 text-xs text-gray-300">
                Total: {item.paieValidations.acompteNetCheck.total?.toFixed(2) || '0.00'}
              </div>
              {item.paieValidations.acompteNetCheck.status === 'Montant élevé' && (
                <div className="mt-1 text-xs text-yellow-300">
                  <Info className="inline w-3 h-3 mr-1" />
                  Le total dépasse 10,000 MAD
                </div>
              )}
            </>
          )}
        </div> */}
        
        {/* AMO & CNSS Check */}
        <div className={`p-3 rounded-lg ${
          item.paieValidations?.amoCnssCheck?.status === 'Valid' 
            ? 'bg-green-900/20' 
            : 'bg-red-900/20'
        }`}>
          <div className="flex items-center">
            {item.paieValidations?.amoCnssCheck?.status === 'Valid' ? (
              <Check className="w-4 h-4 text-green-400 mr-2" />
            ) : (
              <X className="w-4 h-4 text-red-400 mr-2" />
            )}
            <span className="font-medium text-sm">
              Validation AMO & CNSS: 
            </span>
            <span className={`ml-2 text-sm ${
              item.paieValidations?.amoCnssCheck?.status === 'Valid' 
                ? 'text-green-400' 
                : 'text-red-400'
            }`}>
              {item.paieValidations?.amoCnssCheck?.status || 'Non vérifié'}
            </span>
          </div>
          {item.paieValidations?.amoCnssCheck && (
            <>
              <div className="mt-1 text-xs text-gray-300">
                AMO: {item.paieValidations.amoCnssCheck.amo?.toFixed(2) || '0.00'}
              </div>
              <div className="mt-1 text-xs text-gray-300">
                CNSS: {item.paieValidations.amoCnssCheck.cnss?.toFixed(2) || '0.00'}
              </div>
              {item.paieValidations.amoCnssCheck.status === 'Employé non déclaré' && (
                <div className="mt-1 text-xs text-red-300">
                  <Info className="inline w-3 h-3 mr-1" />
                  AMO ou CNSS est à 0 - Employé non déclaré
                </div>
              )}
            </>
          )}
        </div>
        
        {/* Date d'Embauche Check */}
        <div className={`p-3 rounded-lg ${
          item.paieValidations?.embaucheDateCheck?.status === 'Valid' 
            ? 'bg-green-900/20' 
            : 'bg-purple-900/20'
        }`}>
          <div className="flex items-center">
            {item.paieValidations?.embaucheDateCheck?.status === 'Valid' ? (
              <Check className="w-4 h-4 text-green-400 mr-2" />
            ) : (
              <AlertCircle className="w-4 h-4 text-purple-400 mr-2" />
            )}
            <span className="font-medium text-sm">
              Validation Date d'Embauche: 
            </span>
            <span className={`ml-2 text-sm ${
              item.paieValidations?.embaucheDateCheck?.status === 'Valid' 
                ? 'text-green-400' 
                : 'text-purple-400'
            }`}>
              {item.paieValidations?.embaucheDateCheck?.status || 'Non vérifié'}
            </span>
          </div>
          {item.paieValidations?.embaucheDateCheck && (
            <>
              <div className="mt-1 text-xs text-gray-300">
                Date d'Embauche: {item.paieValidations.embaucheDateCheck.dateEmbauche || 'Non spécifiée'}
              </div>
              <div className="mt-1 text-xs text-gray-300">
                Ancienneté: {item.paieValidations.embaucheDateCheck.anciennete || 'Non calculée'}
              </div>
              {item.paieValidations.embaucheDateCheck.status === 'Fin de Contrat' && (
                <div className="mt-1 text-xs text-purple-300">
                  <Info className="inline w-3 h-3 mr-1" />
                  L'employé a moins de 6 mois d'ancienneté
                </div>
              )}
            </>
          )}
        </div>


        {/* HS 25 comparison */}
        <div className={`p-3 rounded-lg ${
          item.hs25Status === 'Correct' ? 'bg-green-900/20' : 'bg-red-900/20'
        }`}>
          <div className="flex items-center">
            {item.hs25Status === 'Correct' ? (
              <Check className="w-4 h-4 text-green-400 mr-2" />
            ) : (
              <X className="w-4 h-4 text-red-400 mr-2" />
            )}
            <span className="font-medium text-sm">
              HS 25 Pointage vs HS 25 Paie: 
            </span>
            <span className={`ml-2 text-sm ${
              item.hs25Status === 'Correct' ? 'text-green-400' : 'text-red-400'
            }`}>
              {item.hs25Status}
            </span>
          </div>

          {item.hs25Pointage === undefined && item.hs25Paie === undefined ? (
            <div className="text-xs text-gray-500 italic">
              Données HS 25 non disponibles pour cet employé
            </div>
          ) : (
            <>
              {item.hs25Pointage !== undefined && (
                <div className="mt-1 text-xs text-gray-300">
                  HS 25 Pointage: {item.hs25Pointage.toFixed(2)}
                </div>
              )}
              {item.hs25Paie !== undefined && (
                <div className="mt-1 text-xs text-gray-300">
                  HS 25 Paie: {item.hs25Paie.toFixed(2)}
                </div>
              )}
            </>
          )}

          {item.hs25Status === 'Incohérence' && (
            <div className="mt-1 text-xs text-red-300">
              <Info className="inline w-3 h-3 mr-1" />
              Les valeurs devraient être identiques
            </div>
          )}
        </div>
        
        {/* HS 50 comparison - NEW */}
        <div className={`p-3 rounded-lg ${
          item.hs50Status === 'Correct' ? 'bg-green-900/20' : 'bg-red-900/20'
        }`}>
          <div className="flex items-center">
            {item.hs50Status === 'Correct' ? (
              <Check className="w-4 h-4 text-green-400 mr-2" />
            ) : (
              <X className="w-4 h-4 text-red-400 mr-2" />
            )}
            <span className="font-medium text-sm">
              HS 50 Pointage vs HS 50 Paie: 
            </span>
            <span className={`ml-2 text-sm ${
              item.hs50Status === 'Correct' ? 'text-green-400' : 'text-red-400'
            }`}>
              {item.hs50Status}
            </span>
          </div>

          {item.hs50Pointage === undefined && item.hs50Paie === undefined ? (
            <div className="text-xs text-gray-500 italic">
              Données HS 50 non disponibles pour cet employé
            </div>
          ) : (
            <>
              {item.hs50Pointage !== undefined && (
                <div className="mt-1 text-xs text-gray-300">
                  HS 50 Pointage: {item.hs50Pointage.toFixed(2)}
                </div>
              )}
              {item.hs50Paie !== undefined && (
                <div className="mt-1 text-xs text-gray-300">
                  HS 50 Paie: {item.hs50Paie.toFixed(2)}
                </div>
              )}
            </>
          )}

          {item.hs50Status === 'Incohérence' && (
            <div className="mt-1 text-xs text-red-300">
              <Info className="inline w-3 h-3 mr-1" />
              Les valeurs devraient être identiques
            </div>
          )}
        </div>
        
        {/* Hours comparison */}
        <div className={`p-3 rounded-lg ${
          item.difference === 0 ? 'bg-green-900/20' : 'bg-red-900/20'
        }`}>
          <div className="flex items-center">
            {item.difference === 0 ? (
              <Check className="w-4 h-4 text-green-400 mr-2" />
            ) : (
              <X className="w-4 h-4 text-red-400 mr-2" />
            )}
            <span className="font-medium text-sm">
              Validation Heures: 
            </span>
            <span className={`ml-2 text-sm ${
              item.difference === 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              {item.difference === 0 ? 'Correct' : 'Incohérence'}
            </span>
          </div>
          <div className="mt-1 text-xs text-gray-300">
            Heures Pointage: {item.heuresTravaillees?.toFixed(2) || '0.00'}
          </div>
          <div className="mt-1 text-xs text-gray-300">
            Heures Paie: {item.heuresPayees?.toFixed(2) || '0.00'}
          </div>
          {item.difference !== 0 && (
            <div className="mt-1 text-xs text-red-300">
              <Info className="inline w-3 h-3 mr-1" />
              Différence de {Math.abs(item.difference).toFixed(2)} heures
            </div>
          )}
        </div>
        
        {/* Inconsistencies list */}
        {item.inconsistencies && item.inconsistencies.length > 0 && (
          <div className="mt-4 p-3 bg-red-900/20 rounded-lg">
            <h4 className="text-sm font-medium text-red-400 mb-2">Détails des incohérences:</h4>
            <ul className="list-disc list-inside text-xs text-red-300 space-y-1">
              {item.inconsistencies.map((inc, idx) => (
                <li key={idx}>{inc}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </td>
  </tr>
)}







                      </>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {/* Pagination */}
              <div className="mt-6 flex items-center justify-between">
                <div className="text-sm text-gray-400">
                  Affichage de {indexOfFirstRow + 1} à {Math.min(indexOfLastRow, filteredResults.length)} sur {filteredResults.length} résultats
                </div>
                
                <ReactPaginate
                  previousLabel={<ChevronLeft className="h-5 w-5" />}
                  nextLabel={<ChevronRight className="h-5 w-5" />}
                  breakLabel={'...'}
                  pageCount={pageCount}
                  marginPagesDisplayed={2}
                  pageRangeDisplayed={5}
                  onPageChange={handlePageClick}
                  containerClassName="flex items-center space-x-2"
                  pageClassName="flex items-center justify-center h-8 w-8 rounded-md"
                  pageLinkClassName="text-sm font-medium text-gray-300 hover:text-blue-400"
                  activeClassName="bg-blue-900/50 text-blue-400 border border-blue-700"
                  previousClassName="flex items-center justify-center h-8 w-8 rounded-md border border-gray-700 hover:bg-gray-800"
                  nextClassName="flex items-center justify-center h-8 w-8 rounded-md border border-gray-700 hover:bg-gray-800"
                  disabledClassName="opacity-50 cursor-not-allowed"
                  forcePage={currentPage}
                />
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Cobco;