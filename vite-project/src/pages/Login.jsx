import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LogIn } from 'lucide-react';
import Images from "../../src/constant/images";


const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();
    const { signIn } = useAuth();
  
    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        const { error } = await signIn(email, password);
        if (error) throw error;
        navigate('/scif');
      } catch (error) {
        setError('Invalid login credentials');
      }
    };
  

  return (
    <div className="min-h-screen relative bg-[#0D1117] flex flex-col items-center justify-center overflow-hidden">
      {/* Background gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#0D1117] to-[#1A1F2C] opacity-90"></div>
      
      {/* Main content */}
      <div className="relative  z-10 w-full max-w-6xl px-4 md:px-8 mx-auto flex flex-col md:flex-row items-center justify-between">
        {/* Hero Text */}
        <div className="w-full mt-20 md:w-1/2 mb-12 md:mb-0 text-left">
          <h1 className="text-4xl md:text-5xl font-bold mb-6 text-white">
            Contrôlez la cohérence de<br />
            vos <span className="text-[#33C3F0]">données de paie</span>
          </h1>
          <p className="text-gray-300 text-lg mb-8 max-w-xl">
            Détectez instantanément les incohérences entre vos pointages, bulletins
            de paie et factures d'intérimaires. Notre solution automatise les
            vérifications pour plus de précision et moins d'erreurs.
          </p>
         
        </div>
        
        {/* Login Form */}
        <div className="w-full md:w-5/12 bg-[#1A1F2C] p-8 rounded-lg shadow-2xl border border-gray-800">
          <div className="flex items-center justify-center mb-6">
            <LogIn className="w-12 h-12 text-[#33C3F0]" />
          </div>
          <h2 className="text-2xl font-bold text-white text-center mb-6">Admin Login</h2>
          {error && (
            <div className="bg-red-900/30 border border-red-800 text-red-300 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-gray-300 text-sm font-medium mb-2">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 bg-[#242C3D] border border-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-[#33C3F0] focus:border-transparent"
                required
              />
            </div>
            <div className="mb-6">
              <label className="block text-gray-300 text-sm font-medium mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 bg-[#242C3D] border border-gray-700 text-white rounded focus:outline-none focus:ring-2 focus:ring-[#33C3F0] focus:border-transparent"
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-gradient-to-r from-blue-800 to-blue-900 hover:from-blue-800 hover:to-blue-950 text-white py-3 px-4 rounded-full  font-medium transition-colors duration-300"
            >
              Login
            </button>
          </form>
        </div>
      </div>
      
      {/* Logo/Brand */}
      <div className="absolute top-8 left-8 flex items-center">
        
        <img src={Images.logo} alt="Logo" className="h-10 w-10 object-contain" />

        <span className="text-xl font-bold text-white ml-2">SheetSync</span>
      </div>
    </div>
  );
};

export default Login;
