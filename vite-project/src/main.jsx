import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './index.css';
import App from './App.jsx';
import Scif from './pages/scif.jsx';
import Novometal from './pages/novometal.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Router>
      <Routes>
        
        <Route path="/" element={<App />} />
        <Route path="/scif" element={<Scif/>}/>
        <Route path="/novometal" element={<Novometal />} />
      </Routes>
    </Router>
  </StrictMode>,
);