import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import { Layers, RefreshCw, CheckCircle2, AlertCircle, Clock } from 'lucide-react';

export const TopBar: React.FC = () => {
  const { state, resetWorkspaceAction, isLoading } = useAppStore();

  const getStatusBadge = () => {
    switch (state.plan_status) {
      case 'approved':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5" />
            APPROVED
          </span>
        );
      case 'stale':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30">
            <Clock className="w-3.5 h-3.5" />
            STALE
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-sky-500/15 text-sky-400 border border-sky-500/30">
            <AlertCircle className="w-3.5 h-3.5" />
            DRAFT
          </span>
        );
    }
  };

  return (
    <header className="sticky top-0 z-50 bg-[#0f172a]/80 backdrop-blur-xl border-b border-slate-800/80 px-6 py-3">
      <div className="max-w-[1700px] mx-auto flex items-center justify-between flex-wrap gap-4">
        
        {/* Brand & Plan Badges */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-sky-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-sky-500/20">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-extrabold tracking-tight bg-gradient-to-r from-slate-100 to-slate-400 bg-clip-text text-transparent">
                  datasphere-creator
                </h1>
                <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-slate-800 text-sky-400 border border-slate-700">
                  Plan v{state.plan_version || 1}
                </span>
              </div>
              <p className="text-xs text-slate-400">Phase 2 • Automated Modeling Planner</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {getStatusBadge()}
            
            <span className={`px-2.5 py-1 rounded-full text-xs font-mono font-bold border ${
              state.llm_mode === 'REAL' 
                ? 'bg-purple-500/15 text-purple-400 border-purple-500/30' 
                : 'bg-slate-800 text-slate-400 border-slate-700'
            }`}>
              <span className="inline-block w-2 h-2 rounded-full mr-1.5 bg-current animate-pulse" />
              {state.llm_mode}
            </span>
          </div>
        </div>

        {/* Pipeline Stepper */}
        <nav className="flex items-center bg-slate-900/90 px-3 py-1.5 rounded-full border border-slate-800 text-xs">
          <div className="flex items-center gap-1.5 text-sky-400 font-semibold px-2 py-0.5 rounded-full bg-sky-500/10 border border-sky-500/30">
            <span className="w-4 h-4 rounded-full bg-sky-500 text-slate-950 flex items-center justify-center text-[10px] font-bold">1</span>
            <span>Source</span>
          </div>

          <div className="w-4 h-px bg-slate-700 mx-1" />

          <div className="flex items-center gap-1.5 text-indigo-400 font-semibold px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/30">
            <span className="w-4 h-4 rounded-full bg-indigo-500 text-slate-950 flex items-center justify-center text-[10px] font-bold">2</span>
            <span>Plan</span>
          </div>

          <div className="w-4 h-px bg-slate-700 mx-1" />

          <div className="flex items-center gap-1.5 text-slate-500 px-2 py-0.5" title="Coming in Phase 3+">
            <span className="w-4 h-4 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center text-[10px]">3</span>
            <span>Fact View</span>
            <span className="text-[10px] text-slate-600">(Phase 3+)</span>
          </div>

          <div className="w-4 h-px bg-slate-700 mx-1" />

          <div className="flex items-center gap-1.5 text-slate-500 px-2 py-0.5" title="Coming in Phase 3+">
            <span className="w-4 h-4 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center text-[10px]">4</span>
            <span>Graphical</span>
          </div>

          <div className="w-4 h-px bg-slate-700 mx-1" />

          <div className="flex items-center gap-1.5 text-slate-500 px-2 py-0.5" title="Coming in Phase 3+">
            <span className="w-4 h-4 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center text-[10px]">5</span>
            <span>Model</span>
          </div>
        </nav>

        {/* Global Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={resetWorkspaceAction}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-400 hover:text-slate-200 bg-slate-800/60 hover:bg-slate-800 border border-slate-700 rounded-lg transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Reset Workspace
          </button>
        </div>

      </div>
    </header>
  );
};
