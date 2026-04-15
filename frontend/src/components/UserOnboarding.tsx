import React, { useState } from 'react';
import { User, ArrowRight, ShieldCheck, Zap } from 'lucide-react';

interface OnboardingProps {
  onLogin: (name: string) => void;
}

export const UserOnboarding: React.FC<OnboardingProps> = ({ onLogin }) => {
  const [name, setName] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) onLogin(name.trim());
  };

  return (
    <div className="fixed inset-0 bg-slate-950 flex items-center justify-center p-6 z-[100] overflow-hidden">
      {/* Background Decorative Elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/10 blur-[120px] rounded-full"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-600/10 blur-[120px] rounded-full"></div>
      
      <div className="max-w-md w-full relative">
        {/* Logo Section */}
        <div className="text-center mb-12">
          <div className="inline-flex h-20 w-20 rounded-3xl bg-gradient-to-br from-blue-600 to-indigo-600 items-center justify-center mb-6 shadow-2xl shadow-blue-500/20 transform hover:scale-110 transition-transform cursor-pointer">
            <Zap size={40} className="text-white fill-white" />
          </div>
          <h1 className="text-4xl font-black text-white tracking-tight mb-2 uppercase">Protocol v2.0</h1>
          <p className="text-slate-500 font-bold uppercase tracking-[0.2em] text-[10px]">Professional Agentic AI Ecosystem</p>
        </div>

        <div className="bg-slate-900/40 backdrop-blur-3xl border border-slate-800 p-8 rounded-[2.5rem] shadow-2xl shadow-black/50">
          <div className="mb-8">
            <h2 className="text-xl font-bold text-white mb-2">Identify Workspace</h2>
            <p className="text-slate-400 text-sm leading-relaxed">Enter your Professional ID to access your historical sprints, task backlogs, and codebase.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-16 flex items-center pointer-events-none transition-all group-focus-within:text-blue-500 text-slate-500">
                <User size={18} />
              </div>
              <input
                type="text"
                placeholder="Professional ID (e.g. CEO_ADMIN)"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 text-white pl-12 pr-4 py-4 rounded-2xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all outline-none font-bold text-sm"
              />
            </div>

            <button
              type="submit"
              disabled={!name.trim()}
              className="w-full py-4 bg-white hover:bg-slate-100 disabled:opacity-50 disabled:cursor-not-allowed text-slate-950 rounded-2xl font-black uppercase text-xs tracking-widest flex items-center justify-center gap-3 transition-all active:scale-95 shadow-xl shadow-white/5"
            >
              Initialize Workspace <ArrowRight size={16} />
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-slate-800/50 flex items-center justify-center gap-6 opacity-30">
             <div className="flex items-center gap-2 text-[10px] font-bold text-slate-400">
                <ShieldCheck size={14} /> PERSISTENT
             </div>
             <div className="w-1 h-1 rounded-full bg-slate-700"></div>
             <div className="flex items-center gap-2 text-[10px] font-bold text-slate-400">
                <Zap size={14} /> LOW-LATENCY
             </div>
          </div>
        </div>
        
        <p className="text-center mt-8 text-[10px] text-slate-600 font-bold uppercase tracking-widest">
           Handover Protocol Initialized • Antigravity AI Refactor
        </p>
      </div>
    </div>
  );
};
