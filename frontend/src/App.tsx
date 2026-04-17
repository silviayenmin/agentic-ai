import React, { useState, useEffect, useRef } from 'react';
import { 
  Rocket, 
  Terminal, 
  Layout, 
  ClipboardList, 
  Code, 
  Bug, 
  HardDrive, 
  Loader2, 
  CheckCircle2, 
  AlertCircle,
  FileCode,
  ChevronRight,
  Settings,
  RocketIcon,
  Zap,
  CheckCircle,
  Download,
  FileSearch
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sidebar } from './components/Sidebar';
import { UserOnboarding } from './components/UserOnboarding';
import { cn } from './lib/utils';

// --- Types ---
interface Sprint {
  id: number;
  title: string;
  goal: string;
  features: string[];
}

interface Task {
  id: number;
  title: string;
  description: string;
  assigned_to: string;
  priority: 'High' | 'Medium' | 'Low';
}

interface QAReport {
  status: 'PASSED' | 'FAILED';
  bugs: string[];
  suggestions: string[];
}

interface AgentState {
  project_id?: string;
  user_id?: string;
  agent_statuses: Record<string, 'idle' | 'working' | 'done' | 'failed'>;
  current_agent: string;
  sprints: Sprint[];
  tasks: Task[];
  codebase: Record<string, string>;
  qa_report: QAReport;
}

interface ProjectSummary {
  project_id: string;
  requirements: string;
  updated_at: string;
}

export default function App() {
  const [userId, setUserId] = useState<string | null>(localStorage.getItem('agentic_user_id'));
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  
  const [requirements, setRequirements] = useState("");
  const [logs, setLogs] = useState<string[]>([]);
  const [state, setState] = useState<AgentState>({
    agent_statuses: { BA: "idle", PM: "idle", FileChecker: "idle", Dev: "idle", QA: "idle", Monitor: "idle" },
    current_agent: "BA",
    sprints: [],
    tasks: [],
    codebase: {},
    qa_report: { status: 'FAILED', bugs: [], suggestions: [] }
  });
  
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'sprints' | 'tasks' | 'qa' | 'code'>('sprints');
  const scrollRef = useRef<HTMLDivElement>(null);

  // --- WebSocket Connection ---
  useEffect(() => {
    const socket = new WebSocket("ws://localhost:8000/ws");
    socket.onopen = () => console.log("WebSocket Connected");
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "update") {
        setLogs(prev => [...prev, `[${data.agent}] ${data.message}`]);
        setState(data.state);
        
        // Auto-switch tabs based on progress
        if (data.agent === "BA" && data.message.includes("finalized")) setActiveTab('sprints');
        if (data.agent === "PM" && data.message.includes("APPROVED")) setActiveTab('tasks');
        if (data.agent === "QA" && data.message.includes("finished")) setActiveTab('qa');
        if (data.agent === "Dev" && data.message.includes("complete")) setActiveTab('code');
        
        // Final agent completion
        if (data.agent === "Monitor" && data.message.includes("successfully")) {
          setIsRunning(false);
          fetchProjects(); // Refresh sidebar
        }
      }
    };
    socket.onclose = () => setIsRunning(false);
    setWs(socket);
    return () => socket.close();
  }, []);

  // --- Auto-Scroll Logs ---
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  // --- Fetch Projects ---
  const fetchProjects = async () => {
    if (!userId) return;
    try {
      const res = await fetch(`http://localhost:8000/projects?user_id=${userId}`);
      const data = await res.json();
      setProjects(data);
    } catch (e) {
      console.error("Failed to fetch projects", e);
    }
  };

  useEffect(() => {
    if (userId) fetchProjects();
  }, [userId]);

  // --- Actions ---
  const handleLogin = (id: string) => {
    localStorage.setItem('agentic_user_id', id);
    setUserId(id);
  };

  const selectProject = async (id: string) => {
    if (isRunning) return;
    try {
      const res = await fetch(`http://localhost:8000/projects/${id}`);
      const projectState = await res.json();
      setState(projectState);
      setActiveProjectId(id);
      setRequirements(projectState.project_requirements);
      setLogs([`[System] Loaded historical project: ${id}`]);
      setSelectedFile(Object.keys(projectState.codebase)[0] || null);
    } catch (e) {
      console.error("Failed to load project", e);
    }
  };

  const handleNewProject = () => {
    if (isRunning) return;
    setState({
      agent_statuses: { BA: "idle", PM: "idle", FileChecker: "idle", Dev: "idle", QA: "idle", Monitor: "idle" },
      current_agent: "BA",
      sprints: [],
      tasks: [],
      codebase: {},
      qa_report: { status: 'FAILED', bugs: [], suggestions: [] }
    });
    setRequirements("");
    setLogs([]);
    setActiveProjectId(null);
    setSelectedFile(null);
    setActiveTab('sprints');
  };

  const startProject = () => {
    if (ws && requirements && ws.readyState === WebSocket.OPEN && userId) {
      setLogs(["[System] Initializing Agent Ecosystem..."]);
      setState({
        agent_statuses: { BA: "idle", PM: "idle", FileChecker: "idle", Dev: "idle", QA: "idle", Monitor: "idle" },
        current_agent: "BA",
        sprints: [],
        tasks: [],
        codebase: {},
        qa_report: { status: 'FAILED', bugs: [], suggestions: [] }
      });
      setSelectedFile(null);
      setIsRunning(true);
      ws.send(JSON.stringify({ 
        type: "start", 
        requirements,
        user_id: userId 
      }));
    }
  };

  if (!userId) {
    return <UserOnboarding onLogin={handleLogin} />;
  }

  return (
    <div className="flex h-screen bg-[#060b13] text-slate-200 overflow-hidden font-sans selection:bg-blue-500/30">
      <Sidebar 
        projects={projects}
        activeProjectId={activeProjectId}
        onSelectProject={selectProject}
        onNewProject={handleNewProject}
        userName={userId}
      />

      <main className="flex-1 flex flex-col overflow-hidden relative">
        {/* Header Overlay - Classic Dashboard Style */}
        <header className="h-20 border-b border-white/5 flex items-center justify-between px-10 bg-[#060b13] z-10 shrink-0">
          <div className="flex flex-col">
            <h1 className="text-2xl font-black tracking-tighter text-blue-500 flex items-center gap-2">
              AGENTIC AI <span className="text-white opacity-80 font-light tracking-[0.2em] relative -top-0.5">DASHBOARD</span>
            </h1>
            <p className="text-[9px] font-bold text-slate-500 uppercase tracking-[0.3em] mt-0.5">Multi-Agent Development Protocol v2.5</p>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3 bg-slate-900/40 border border-white/5 px-4 py-2 rounded-full">
              <div className={cn("h-1.5 w-1.5 rounded-full", ws?.readyState === 1 ? "bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" : "bg-red-500")}></div>
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">{ws?.readyState === 1 ? 'Socket Active' : 'Offline'}</span>
            </div>
            <button className="h-10 w-10 flex items-center justify-center rounded-xl bg-slate-900/40 border border-white/5 text-slate-500 hover:text-white transition-colors">
              <Settings size={18} />
            </button>
          </div>
        </header>

        {/* Workspace Body - Two Column Grid */}
        <div className="flex-1 overflow-hidden p-8 flex flex-col gap-6">
          
          {/* Top Row: Navigation/Agent Status */}
          <div className="flex items-start gap-6 h-[180px] shrink-0">
             {/* Left: Metric Summary Column (Responsive thin) */}
             <div className="w-[380px] h-full flex flex-col gap-4">
                <div className="flex-1 bg-slate-900/30 border border-white/5 rounded-2xl p-6 relative overflow-hidden group">
                  <div className="absolute top-0 left-0 w-1 h-full bg-blue-500/50"></div>
                  <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                    <Rocket size={14} className="text-blue-500" /> Project Brief
                  </h3>
                  <textarea 
                    className="w-full h-full bg-transparent text-sm font-medium text-slate-300 placeholder:text-slate-700 outline-none resize-none scrollbar-none pb-4"
                    placeholder="What are we building today?"
                    value={requirements}
                    onChange={(e) => setRequirements(e.target.value)}
                    disabled={isRunning}
                  ></textarea>
                </div>
             </div>

             {/* Right: Agent Grid (Full Wide) */}
             <div className="flex-1 h-full grid grid-cols-6 gap-4">
                <AgentCard name="BA" role="Architect" status={state.agent_statuses.BA} isCurrent={state.current_agent === 'BA'} />
                <AgentCard name="PM" role="Planner" status={state.agent_statuses.PM} isCurrent={state.current_agent === 'PM'} />
                <AgentCard name="FileChecker" role="Checker" status={state.agent_statuses.FileChecker} isCurrent={state.current_agent === 'FileChecker'} />
                <AgentCard name="Dev" role="Developer" status={state.agent_statuses.Dev} isCurrent={state.current_agent === 'Dev'} />
                <AgentCard name="QA" role="Critic" status={state.agent_statuses.QA} isCurrent={state.current_agent === 'QA'} />
                <AgentCard name="Monitor" role="Deployer" status={state.agent_statuses.Monitor} isCurrent={state.current_agent === 'Monitor'} />
             </div>
          </div>

          {/* Bottom Row: Controls & Tabs */}
          <div className="flex-1 flex gap-6 overflow-hidden">
             {/* Left Column: Action & Metrics */}
             <div className="w-[380px] flex flex-col gap-4 shrink-0">
                <button 
                  onClick={startProject}
                  disabled={isRunning || !requirements}
                  className={cn(
                    "w-full h-16 rounded-2xl font-black text-[11px] uppercase tracking-[0.3em] transition-all flex items-center justify-center gap-3 border shadow-2xl",
                    isRunning 
                      ? "bg-slate-900/50 border-white/5 text-slate-600 cursor-not-allowed" 
                      : "bg-white text-slate-950 border-white hover:bg-slate-100 hover:scale-[1.01] active:scale-95 shadow-white/5"
                  )}
                >
                  {isRunning ? <Loader2 size={18} className="animate-spin" /> : <RocketIcon size={18} />}
                  {isRunning ? 'Systems Active' : 'Initialize Build'}
                </button>

                <div className="grid grid-cols-2 gap-4 flex-1 pb-4">
                  <div className="bg-slate-900/30 border border-white/5 p-6 rounded-2xl flex flex-col justify-between">
                     <span className="text-[9px] font-black uppercase tracking-widest text-slate-500">Tasks Assigned</span>
                     <span className="text-3xl font-mono text-white mt-2">{state.tasks.length}</span>
                  </div>
                  <div className="bg-slate-900/30 border border-white/5 p-6 rounded-2xl flex flex-col justify-between">
                     <span className="text-[9px] font-black uppercase tracking-widest text-slate-500">Files Written</span>
                     <span className="text-3xl font-mono text-white mt-2">{Object.keys(state.codebase).length}</span>
                  </div>
                </div>

                <div className="h-[200px] bg-slate-950/50 border border-white/5 rounded-2xl p-6 overflow-hidden flex flex-col">
                  <h3 className="text-[10px] font-black text-slate-600 uppercase tracking-widest mb-4">Live Logs</h3>
                  <div ref={scrollRef} className="flex-1 overflow-auto font-mono text-[9px] text-slate-500 space-y-2 scrollbar-none pb-4">
                    {logs.map((log, i) => <div key={i} className="whitespace-pre-wrap">{log}</div>)}
                    {logs.length === 0 && <div className="italic">Console Standby...</div>}
                  </div>
                </div>
             </div>

             {/* Right Column: Main Area Tabs */}
             <div className="flex-1 bg-slate-900/20 border border-white/5 rounded-[2rem] overflow-hidden flex flex-col shadow-3xl">
                <div className="flex items-center gap-10 px-10 border-b border-white/5 bg-[#0a1019]">
                   {[
                    { id: 'sprints', icon: Layout, label: 'Sprints' },
                    { id: 'tasks', icon: ClipboardList, label: 'Backlog' },
                    { id: 'code', icon: Code, label: 'Workspace' },
                    { id: 'qa', icon: Bug, label: 'QA Status' }
                  ].map((tab) => (
                    <button 
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id as any)}
                      className={cn(
                        "flex items-center gap-2 py-6 text-[10px] font-black uppercase tracking-widest transition-all relative",
                        activeTab === tab.id ? "text-blue-500" : "text-slate-500 hover:text-slate-300"
                      )}
                    >
                      <tab.icon size={14} />
                      {tab.label}
                      {activeTab === tab.id && (
                        <motion.div layoutId="classic-nav" className="absolute bottom-0 left-0 right-0 h-1 bg-blue-500 rounded-t" />
                      )}
                    </button>
                  ))}
                </div>

                <div className="flex-1 p-10 overflow-auto custom-scrollbar">
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={activeTab}
                      initial={{ opacity: 0, scale: 0.98 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.98 }}
                      transition={{ duration: 0.15 }}
                      className="h-full"
                    >
                    {activeTab === 'sprints' && (
                      <div className="grid grid-cols-2 gap-4">
                        {state.sprints.length > 0 ? (
                          state.sprints.map((sprint, i) => (
                            <div key={i} className="bg-slate-800/20 border border-slate-800/80 p-6 rounded-3xl hover:border-blue-500/30 transition-all">
                              <div className="flex items-center gap-3 mb-4">
                                <span className="text-[9px] font-mono bg-blue-500 text-white px-2 py-0.5 rounded uppercase font-black">PHASE {sprint.id}</span>
                                <h4 className="font-black text-sm text-slate-100 uppercase tracking-tight">{sprint.title}</h4>
                              </div>
                              <p className="text-xs text-slate-400 mb-6 leading-relaxed font-medium">{sprint.goal}</p>
                              <div className="flex flex-wrap gap-2">
                                {sprint.features.map((f, j) => (
                                  <span key={j} className="text-[9px] text-slate-500 bg-slate-950/50 px-3 py-1.5 rounded-xl border border-slate-800 font-bold uppercase tracking-tighter">{f}</span>
                                ))}
                              </div>
                            </div>
                          ))
                        ) : <EmptyState isLoading={isRunning} message={isRunning ? "Defining architecture..." : "Systems Ready"} />}
                      </div>
                    )}

                    {activeTab === 'tasks' && (
                      <div className="grid grid-cols-1 gap-3">
                        {state.tasks.length > 0 ? (
                          state.tasks.map((task, i) => (
                            <div key={i} className="flex items-center justify-between bg-slate-800/20 border border-slate-800/80 p-4 rounded-2xl group hover:border-white/10 transition-colors">
                              <div className="flex items-center gap-4">
                                <div className={cn(
                                  "h-1.5 w-1.5 rounded-full shadow-[0_0_8px_rgba(0,0,0,0.5)]",
                                  task.priority === 'High' ? "bg-rose-500" : task.priority === 'Medium' ? "bg-amber-500" : "bg-blue-500"
                                )}></div>
                                <div>
                                  <h4 className="text-sm font-black text-slate-100 uppercase tracking-tight">{task.title}</h4>
                                  <p className="text-[10px] text-slate-500 font-medium">{task.description}</p>
                                </div>
                              </div>
                              <div className="flex items-center gap-4">
                                <span className="text-[9px] font-black text-slate-500 border border-slate-800 px-3 py-1 rounded-full uppercase tracking-widest bg-slate-950">@{task.assigned_to}</span>
                                <ChevronRight size={14} className="text-slate-800 group-hover:text-slate-600" />
                              </div>
                            </div>
                          ))
                        ) : <EmptyState isLoading={isRunning} message={isRunning ? "Planning workflow..." : "Awaiting Tasking"} />}
                      </div>
                    )}

                    {activeTab === 'code' && (
                      <div className="grid grid-cols-12 gap-8 h-full">
                        <div className="col-span-12 xl:col-span-3 space-y-2">
                          {Object.keys(state.codebase).map(filename => (
                            <button 
                              key={filename}
                              onClick={() => setSelectedFile(filename)}
                              className={cn(
                                "w-full text-left p-4 rounded-2xl flex items-center justify-between text-[11px] font-bold transition-all border",
                                selectedFile === filename 
                                  ? "bg-blue-600 border-blue-500 text-white shadow-xl shadow-blue-500/20" 
                                  : "bg-slate-950/50 border-slate-800 hover:border-slate-700 text-slate-500"
                              )}
                            >
                              <div className="flex items-center gap-3">
                                 <FileCode size={16} className={selectedFile === filename ? "text-white" : "text-slate-700"} /> 
                                 <span className="truncate">{filename}</span>
                              </div>
                              {selectedFile === filename && <CheckCircle size={14} />}
                            </button>
                          ))}
                          {Object.keys(state.codebase).length === 0 && <EmptyState isLoading={isRunning} message="Awaiting source generation..." />}
                        </div>
                        <div className="col-span-12 xl:col-span-9 bg-slate-950 rounded-[2rem] p-8 border border-slate-800 overflow-hidden flex flex-col min-h-[400px]">
                          <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-800/50">
                             <div className="flex items-center gap-2">
                                <div className="h-2 w-2 rounded-full bg-blue-500"></div>
                                <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">{selectedFile || 'No file selected'}</span>
                             </div>
                             <div className="flex items-center gap-3">
                                <button className="p-2 hover:bg-slate-900 rounded-lg text-slate-500 transition-colors"><Download size={16}/></button>
                             </div>
                          </div>
                          <div className="flex-1 overflow-auto custom-scrollbar font-mono text-xs leading-relaxed text-slate-300">
                            {selectedFile ? (
                              <pre className="selection:bg-blue-500/40">{state.codebase[selectedFile]}</pre>
                            ) : (
                              <div className="flex flex-col items-center justify-center h-full opacity-10">
                                <Code size={80} />
                                <p className="mt-6 text-xl font-black uppercase tracking-[0.4em]">Standby</p>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}

                    {activeTab === 'qa' && (
                      <div className="space-y-8">
                        {state.qa_report.status ? (
                          <>
                            <div className={cn(
                              "flex items-center gap-6 p-8 rounded-[2rem] border-2",
                              state.qa_report.status === 'PASSED' ? "bg-emerald-500/5 border-emerald-500/20" : "bg-rose-500/5 border-rose-500/20"
                            )}>
                              <div className={cn(
                                "h-16 w-16 rounded-3xl flex items-center justify-center shadow-2xl",
                                state.qa_report.status === 'PASSED' ? "bg-emerald-500 text-white shadow-emerald-500/20" : "bg-rose-500 text-white shadow-rose-500/20"
                              )}>
                                {state.qa_report.status === 'PASSED' ? <CheckCircle2 size={32} /> : <AlertCircle size={32} />}
                              </div>
                              <div>
                                <h3 className="font-black text-2xl text-slate-100 uppercase tracking-tight">Project {state.qa_report.status}</h3>
                                <p className="text-xs text-slate-500 font-bold uppercase tracking-widest mt-1">Audit Protocol v2.4 Finalized</p>
                              </div>
                            </div>
                            <div className="grid grid-cols-2 gap-8">
                              <div className="bg-slate-900/40 p-8 rounded-[2.5rem] border border-slate-800">
                                <h4 className="text-[10px] font-black text-rose-500 uppercase tracking-[0.2em] mb-6 flex items-center gap-2">
                                  <Bug size={14} /> Intelligence Gaps
                                </h4>
                                {state.qa_report.bugs.length > 0 ? (
                                  <ul className="space-y-3">
                                    {state.qa_report.bugs.map((bug, i) => (
                                      <li key={i} className="text-xs text-slate-400 flex items-start gap-4 p-3 bg-rose-500/5 rounded-xl border border-rose-500/10 font-medium">
                                        <div className="h-1.5 w-1.5 rounded-full bg-rose-500 mt-1.5 shrink-0"></div> {bug}
                                      </li>
                                    ))}
                                  </ul>
                                ) : <p className="text-xs text-slate-500 italic font-medium">No system anomalies detected.</p>}
                              </div>
                              <div className="bg-slate-900/40 p-8 rounded-[2.5rem] border border-slate-800">
                                <h4 className="text-[10px] font-black text-blue-500 uppercase tracking-[0.2em] mb-6 flex items-center gap-2">
                                  <Rocket size={14} /> Optimization Map
                                </h4>
                                {state.qa_report.suggestions.length > 0 ? (
                                  <ul className="space-y-3">
                                    {state.qa_report.suggestions.map((s, i) => (
                                      <li key={i} className="text-xs text-slate-400 flex items-start gap-4 p-3 bg-blue-500/5 rounded-xl border border-blue-500/10 font-medium">
                                        <div className="h-1.5 w-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0"></div> {s}
                                      </li>
                                    ))}
                                  </ul>
                                ) : <p className="text-xs text-slate-500 italic font-medium">System operating at peak efficiency.</p>}
                              </div>
                            </div>
                          </>
                        ) : <EmptyState isLoading={isRunning} message="Quality protocols initializing..." />}
                      </div>
                    )}
                    </motion.div>
                  </AnimatePresence>
                </div>
             </div>
          </div>
        </div>
      </main>
    </div>
  );
}

const AgentCard = ({ name, role, status, isCurrent }: { name: string, role: string, status: string, isCurrent: boolean }) => {
  const getColors = () => {
    switch(status) {
      case 'working': return 'border-blue-500/50 bg-blue-500/5';
      case 'done': return 'border-emerald-500/30 bg-emerald-500/5';
      case 'failed': return 'border-rose-500/30 bg-rose-500/5';
      default: return 'border-white/5 bg-slate-900/40 text-slate-600';
    }
  };

  const iconMap = {
    BA: Layout,
    PM: ClipboardList,
    FileChecker: FileSearch,
    Dev: Code,
    QA: Bug,
    Monitor: HardDrive
  };

  const Icon = iconMap[name as keyof typeof iconMap] || Settings;

  return (
    <motion.div 
      className={cn(
        "p-6 rounded-2xl border transition-all duration-300 relative flex flex-col items-center justify-center",
        getColors(),
        isCurrent && "ring-1 ring-blue-500/50 shadow-[0_0_20px_rgba(59,130,246,0.1)]"
      )}
    >
      <div className={cn(
        "mb-3",
        status === 'working' ? "text-blue-500" : status === 'done' ? "text-emerald-500" : "text-slate-600"
      )}>
        <Icon size={24} />
      </div>
      <h3 className="font-black text-[10px] uppercase tracking-wider text-slate-100">{role}</h3>
      <p className="text-[8px] font-bold text-slate-500 uppercase mt-1">Agent {name}</p>
      
      {status === 'working' && (
        <div className="absolute top-4 right-4 flex items-center gap-1.5 px-2 py-0.5 rounded bg-blue-600 text-[8px] font-black text-white uppercase tracking-widest animate-pulse">
           Working
        </div>
      )}
      {status === 'idle' && !isCurrent && (
        <div className="absolute top-4 right-4 px-2 py-0.5 rounded bg-slate-800 text-[8px] font-black text-slate-500 uppercase tracking-widest">
           Idle
        </div>
      )}
    </motion.div>
  );
};

const EmptyState = ({ message, isLoading }: { message: string, isLoading: boolean }) => (
  <div className="flex flex-col items-center justify-center h-full py-20 opacity-20">
    <div className="mb-6 p-6 rounded-[2rem] border-2 border-dashed border-slate-700">
      {isLoading ? <Loader2 size={48} className="animate-spin text-blue-500" /> : <ClipboardList size={48} className="text-slate-500" />}
    </div>
    <p className="text-xl font-black tracking-[0.3em] uppercase">{message}</p>
  </div>
);
