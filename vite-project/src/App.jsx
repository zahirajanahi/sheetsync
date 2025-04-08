import React from 'react';
import Images from "../src/constant/images";

const App = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-black font-sans">
      {/* Header */}
      <header className="container mx-auto px-6 py-8">
        <nav className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src={Images.logo} alt="Logo" className="h-10 w-10 object-contain" />
            <span className="text-white text-xl font-semibold tracking-tight">SheetSync</span>
          </div>
          
          <div className="flex items-center gap-4">
            <button className="text-gray-100 hover:text-white px-6 py-2.5 rounded-full bg-white/10 backdrop-blur-lg border border-white/10 transition-all duration-300 hover:bg-white/15">
              Se connecter
            </button>
          </div>
        </nav>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 mt-10 mb-20">
        <div className="grid md:grid-cols-2 gap-16 items-center">
          {/* Left Column */}
          <div className="space-y-8">
            <span className="inline-block px-4 py-1.5 bg-blue-500/10 text-blue-400 rounded-full text-sm font-medium border border-blue-500/20">
              Vérification de paie simplifiée
            </span>
            
            <h1 className="text-4xl sm:text-5xl font-bold text-white leading-tight">
              Contrôlez la cohérence de vos <span className="bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">données de paie</span>
            </h1>
            
            <p className="text-slate-400 text-lg leading-relaxed">
              Détectez instantanément les incohérences entre vos pointages, bulletins de paie et factures d'intérimaires. Notre solution automatise les vérifications pour plus de précision et moins d'erreurs.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 pt-2">
              <a href="/scif" className="bg-gradient-to-r from-blue-800 to-blue-900 hover:from-blue-800 hover:to-blue-950 text-white px-8 py-3.5 rounded-xl font-medium transition-all duration-300 shadow-lg ">
                Commencer maintenant
              </a>
            </div>
          </div>

          {/* Right Column - Dashboard Preview */}
          <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-8 shadow-[0_8px_30px_rgb(0,0,0,0.12)]">
            <h2 className="text-2xl font-semibold text-white mb-6">Vérification Pointage vs Paie</h2>
            
            {/* Stats Grid */}
            <div className="grid grid-cols-3 gap-4 mb-8">
              <div className="bg-white/5 backdrop-blur-sm p-4 rounded-xl border border-white/5">
                <p className="text-slate-400 text-sm">Total employés</p>
                <p className="text-2xl font-bold text-white mt-1">337</p>
              </div>
              <div className="bg-white/5 backdrop-blur-sm p-4 rounded-xl border border-white/5">
                <p className="text-slate-400 text-sm">Correspondances</p>
                <p className="text-2xl font-bold text-emerald-400 mt-1">259</p>
              </div>
              <div className="bg-white/5 backdrop-blur-sm p-4 rounded-xl border border-white/5">
                <p className="text-slate-400 text-sm">Incohérences</p>
                <p className="text-2xl font-bold text-rose-400 mt-1">78</p>
              </div>
            </div>

            {/* Table */}
            <div className="bg-white/5 backdrop-blur-sm rounded-xl overflow-hidden border border-white/5">
              <div className="grid grid-cols-4 gap-4 p-4 border-b border-white/10 text-sm font-medium text-slate-300">
                <div>NOM ET PRÉNOM</div>
                <div>POINTAGE</div>
                <div>PAIE</div>
                <div className="text-right">STATUT</div>
              </div>

              <div className="divide-y divide-white/5">
                <div className="grid grid-cols-4 gap-4 p-4 text-sm hover:bg-white/5 transition-colors">
                  <div className="text-white font-medium">MARTIN S.</div>
                  <div className="text-slate-300">35.00</div>
                  <div className="text-slate-300">35.00</div>
                  <div className="text-right">
                    <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full text-xs">
                      Correct
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-4 p-4 text-sm hover:bg-white/5 transition-colors">
                  <div className="text-white font-medium">DUBOIS M.</div>
                  <div className="text-slate-300">0.00</div>
                  <div className="text-slate-300">40.00</div>
                  <div className="text-right">
                    <span className="px-3 py-1 bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-full text-xs">
                      Erreur
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-4 p-4 text-sm hover:bg-white/5 transition-colors">
                  <div className="text-white font-medium">LAURENT T.</div>
                  <div className="text-slate-300">42.50</div>
                  <div className="text-slate-300">40.00</div>
                  <div className="text-right">
                    <span className="px-3 py-1 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-full text-xs">
                      Alerte
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;