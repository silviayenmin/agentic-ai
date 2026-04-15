import React from 'react';
import { Plus, History, Briefcase, ChevronRight, Clock } from 'lucide-react';
import { cn } from '../lib/utils'; // Assuming I'll create or use a helper

interface Project {
  project_id: string;
  requirements: string;
  updated_at: string;
}

interface SidebarProps {
  projects: Project[];
  activeProjectId: string | null;
  onSelectProject: (id: string) => void;
  onNewProject: () => void;
  userName: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  projects, 
  activeProjectId, 
  onSelectProject, 
  onNewProject,
  userName
}) => {
  return (
    <aside className="w-80 h-full bg-slate-950 border-r border-slate-800 flex flex-col transition-all duration-300">
      {/* Header */}
      <div className="p-6 flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center font-bold text-lg text-white shadow-lg shadow-blue-500/20">
            A
          </div>
          <div>
            <h1 className="text-sm font-black tracking-widest text-white uppercase">Agentic AI</h1>
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-tighter">Pro Workspace</p>
          </div>
        </div>
        
        <button 
          onClick={onNewProject}
          className="w-full py-3 bg-white hover:bg-slate-100 text-slate-900 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all active:scale-95 shadow-lg shadow-white/5"
        >
          <Plus size={18} /> New Project
        </button>
      </div>

      {/* History */}
      <div className="flex-1 overflow-y-auto px-4 space-y-6">
        <div>
          <h2 className="px-2 text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4 flex items-center gap-2">
            <History size={12} /> Project History
          </h2>
          <div className="space-y-1">
            {projects.map((project) => (
              <button
                key={project.project_id}
                onClick={() => onSelectProject(project.project_id)}
                className={cn(
                  "w-full text-left p-3 rounded-xl group transition-all flex items-center gap-3 relative overflow-hidden",
                  activeProjectId === project.project_id 
                    ? "bg-blue-600/10 border border-blue-500/30 text-blue-400" 
                    : "hover:bg-slate-900 border border-transparent text-slate-400"
                )}
              >
                {activeProjectId === project.project_id && (
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]"></div>
                )}
                <div className={cn(
                  "h-8 w-8 rounded-lg flex items-center justify-center shrink-0 border transition-all",
                  activeProjectId === project.project_id 
                    ? "bg-blue-500/20 border-blue-500/50" 
                    : "bg-slate-800 border-slate-700 group-hover:border-slate-600"
                )}>
                  <Briefcase size={14} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-bold truncate">{project.requirements}</p>
                  <div className="flex items-center gap-1 text-[9px] text-slate-500 font-mono mt-0.5">
                    <Clock size={10} />
                    {new Date(project.updated_at).toLocaleDateString()}
                  </div>
                </div>
                <ChevronRight size={14} className={cn(
                  "opacity-0 transition-opacity",
                  activeProjectId === project.project_id ? "opacity-100" : "group-hover:opacity-100"
                )} />
              </button>
            ))}
            {projects.length === 0 && (
              <div className="p-8 text-center opacity-20 flex flex-col items-center gap-3 grayscale">
                 <History size={32} />
                 <p className="text-[10px] font-bold uppercase tracking-widest">No history yet</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-slate-800 mt-auto">
        <div className="flex items-center gap-3 p-3 bg-slate-900/40 rounded-2xl border border-slate-800/50">
          <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-slate-700 to-slate-800 border border-slate-600 flex items-center justify-center text-[10px] font-bold text-slate-300 uppercase">
            {userName.slice(0, 2)}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[10px] font-black text-slate-200 truncate uppercase tracking-tighter">{userName}</p>
            <div className="flex items-center gap-1">
              <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
              <p className="text-[9px] text-slate-500 font-mono">Workspace Active</p>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};
