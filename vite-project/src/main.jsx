import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './index.css';
import App from './App.jsx';
import Login from './pages/Login.jsx';
import Scif from './pages/scif.jsx';
import Novometal from './pages/novometal.jsx';
import Cobco from './pages/cobco.jsx';
import CasaEaro from './pages/casaEaro.jsx';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import Sbbc from './pages/sbbc.jsx';
import Other from './pages/other.jsx';
import Temp from './pages/template.jsx';
import TempT from './pages/temp.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/login" element={<Login />} />

          <Route path='/temp'  element={
              <ProtectedRoute>
                <Temp />
              </ProtectedRoute>
            } />

          <Route path='/temp2'  element={
              <ProtectedRoute>
                <TempT />
              </ProtectedRoute>
            } />


          <Route path='/sbbc'  element={
              <ProtectedRoute>
                <Sbbc />
              </ProtectedRoute>
            } />
              <Route path='/other'  element={
              <ProtectedRoute>
                <Other />
              </ProtectedRoute>
            } />
          <Route
            path="/scif"
            element={
              <ProtectedRoute>
                <Scif />
              </ProtectedRoute>
            }
          />
          <Route
            path="/novometal"
            element={
              <ProtectedRoute>
                <Novometal />
              </ProtectedRoute>
            }
          />
          <Route
            path="/cobco"
            element={
              <ProtectedRoute>
                <Cobco />
              </ProtectedRoute>
            }
          />
          <Route
            path="/casaEaro"
            element={
              <ProtectedRoute>
                <CasaEaro />
              </ProtectedRoute>
            }
          />
        </Routes>
      </Router>
    </AuthProvider>
  </StrictMode>
);