import React from 'react';
import { Link } from 'react-router-dom';


function App() {

  return (
 
        <>
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
        </>
                
  );
}

export default App;