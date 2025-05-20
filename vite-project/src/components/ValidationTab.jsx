import React, { useState } from 'react';
import { AlertTriangle, DollarSign, User, Calendar, Search } from 'lucide-react';
import ReactPaginate from 'react-paginate';

const ValidationTab = ({ validationResults }) => {
  const [currentPage, setCurrentPage] = useState(0);
  const [rowsPerPage] = useState(10);
  const [filterType, setFilterType] = useState('all');
  const [cinFilter, setCinFilter] = useState('');
  
  // Filter results based on type and CIN
  const filteredResults = validationResults?.filter(item => {
    // Type filter
    const typeMatch = filterType === 'all' || 
      item.issues.some(issue => issue.type === filterType);
    
    // CIN filter
    const cinMatch = cinFilter === '' || 
      item.CIN.toLowerCase().includes(cinFilter.toLowerCase());
    
    return typeMatch && cinMatch;
  }) || [];
  
  // Pagination calculations
  const indexOfLastRow = (currentPage + 1) * rowsPerPage;
  const indexOfFirstRow = currentPage * rowsPerPage;
  const currentRows = filteredResults.slice(indexOfFirstRow, indexOfLastRow);
  const pageCount = Math.ceil(filteredResults.length / rowsPerPage);
  
  const handlePageClick = ({ selected }) => {
    setCurrentPage(selected);
  };
  
  const getIconForIssue = (type) => {
    switch(type) {
      case 'montant_eleve':
        return <DollarSign className="w-5 h-5 text-yellow-400" />;
      case 'non_declare':
        return <User className="w-5 h-5 text-red-400" />;
      case 'contrat_court':
        return <Calendar className="w-5 h-5 text-blue-400" />;
      default:
        return <AlertTriangle className="w-5 h-5 text-orange-400" />;
    }
  };
  
  const getStatusBadge = (type) => {
    switch(type) {
      case 'montant_eleve':
        return 'bg-yellow-900/50 text-yellow-400 border border-yellow-700';
      case 'non_declare':
        return 'bg-red-900/50 text-red-400 border border-red-700';
      case 'contrat_court':
        return 'bg-blue-900/50 text-blue-400 border border-blue-700';
      default:
        return 'bg-orange-900/50 text-orange-400 border border-orange-700';
    }
  };
  
  const getStatusText = (type) => {
    switch(type) {
      case 'montant_eleve':
        return 'Montant élevé';
      case 'non_declare':
        return 'Employé non déclaré';
      case 'contrat_court':
        return 'Contrat < 6 mois';
      default:
        return 'Anomalie';
    }
  };
  
  // If no validation results
  if (!validationResults || validationResults.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-900/30 mb-4">
          <Check className="w-8 h-8 text-green-400" />
        </div>
        <h3 className="text-lg font-medium text-gray-300">Aucune anomalie détectée</h3>
        <p className="mt-2 text-sm text-gray-400">
          Le fichier de journal de paie ne présente aucune anomalie selon les critères de validation.
        </p>
      </div>
    );
  }
  
  return (
    <div className="mt-8">
      {/* Filters */}
      <div className="mb-4 flex flex-col md:flex-row gap-4">
        <div className="w-full md:w-64">
          <label htmlFor="cinValidationFilter" className="block text-sm font-medium text-gray-300 mb-1">
            Filtrer par CIN
          </label>
          <div className="relative">
            <input
              type="text"
              id="cinValidationFilter"
              value={cinFilter}
              onChange={(e) => {
                setCinFilter(e.target.value);
                setCurrentPage(0);
              }}
              placeholder="Rechercher par CIN..."
              className="w-full bg-gray-800 border border-gray-700 text-gray-300 rounded-md pl-9 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-500" />
          </div>
        </div>
        
        <div className="w-full md:w-64">
          <label htmlFor="typeFilter" className="block text-sm font-medium text-gray-300 mb-1">
            Filtrer par type d'anomalie
          </label>
          <select
            id="typeFilter"
            value={filterType}
            onChange={(e) => {
              setFilterType(e.target.value);
              setCurrentPage(0);
            }}
            className="w-full bg-gray-800 border border-gray-700 text-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">Tous les types</option>
            <option value="montant_eleve">Montant élevé</option>
            <option value="non_declare">Employé non déclaré</option>
            <option value="contrat_court">Contrat  6 mois</option>
          </select>
        </div>
      </div>
      
      {/* Results table */}
      <div className="overflow-x-auto rounded-lg border border-gray-700 shadow-xl backdrop-blur-sm">
        <table className="min-w-full divide-y divide-gray-700">
          <thead className="bg-gray-800">
            <tr>
              <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                CIN
              </th>
              <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Type d'anomalie
              </th>
              <th scope="col" className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Détails
              </th>
            </tr>
          </thead>
          <tbody className="bg-gray-900 divide-y divide-gray-800">
            {currentRows.map((item, index) => (
              // For each employee with validation issues
              item.issues.map((issue, issueIndex) => (
                <tr 
                  key={`${index}-${issueIndex}`} 
                  className={`hover:bg-gray-800/50`}
                  style={{ transition: 'background-color 0.2s ease' }}
                >
                  {/* Only show CIN on first issue row for this employee */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-200">
                    {issueIndex === 0 ? item.CIN : ''}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getIconForIssue(issue.type)}
                      <span className={`ml-2 px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadge(issue.type)}`}>
                        {getStatusText(issue.type)}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-300">
                    <div className="flex flex-col">
                      <span>{issue.message}</span>
                      
                      {/* Conditionally show details based on issue type */}
                      {issue.type === 'montant_eleve' && (
                        <div className="text-xs text-gray-400 mt-1">
                          Acompte: {issue.acompte?.toFixed(2)} MAD | Net Payé: {issue.net_paye?.toFixed(2)} MAD | Total: {issue.total?.toFixed(2)} MAD
                        </div>
                      )}
                      
                      {issue.type === 'non_declare' && (
                        <div className="text-xs text-gray-400 mt-1">
                          AMO: {issue.amo === 0 ? 'Non déclaré' : 'Déclaré'} | CNSS: {issue.cnss === 0 ? 'Non déclaré' : 'Déclaré'}
                        </div>
                      )}
                      
                      {issue.type === 'contrat_court' && (
                        <div className="text-xs text-gray-400 mt-1">
                          Date d'embauche: {issue.date_embauche} | Durée: {issue.months_employed} mois
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            ))}
          </tbody>
        </table>
      </div>
      
      {/* Pagination */}
      {pageCount > 1 && (
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
      )}
    </div>
  );
};

export default ValidationTab;