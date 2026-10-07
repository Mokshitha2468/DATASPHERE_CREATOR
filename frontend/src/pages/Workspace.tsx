import React, { useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';
import { TopBar } from '../components/layout/TopBar';
import { LeftPanel } from '../components/layout/LeftPanel';
import { VisualFlow } from '../components/plan/VisualFlow';
import { ColumnsTable } from '../components/plan/ColumnsTable';
import { FiltersManager } from '../components/plan/FiltersManager';
import { JsonEditor } from '../components/plan/JsonEditor';
import { HistoryViewer } from '../components/plan/HistoryViewer';
import { ActionFooter } from '../components/plan/ActionFooter';
import { LiveTimeline } from '../components/logs/LiveTimeline';
import { ToastContainer } from '../components/common/Toast';
import { subscribeLogStream } from '../api/sse';
import { Eye, Columns, Filter, Code2, History } from 'lucide-react';

export const Workspace: React.FC = () => {
  const {
    activeCenterTab,
    setActiveCenterTab,
    loadInitialState,
    addAgentEvent,
    state
  } = useAppStore();

  useEffect(() => {
    loadInitialState();

    // Subscribe to live agent SSE event stream
    const unsubscribe = subscribeLogStream((event) => {
      addAgentEvent(event);
    });

    return () => {
      unsubscribe();
    };
  }, []);

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-[#080c14] text-slate-100">
      {/* Top Bar */}
      <TopBar />

      {/* Main 3-Column Layout */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Left Column */}
        <LeftPanel />

        {/* Center Column: Plan Workspace */}
        <main className="flex-1 flex flex-col min-w-0 bg-slate-950 overflow-hidden">
          
          {/* Center Tabs Navigation */}
          <div className="border-b border-slate-800/80 bg-slate-900/60 px-4 py-2 flex items-center justify-between">
            <div className="flex items-center gap-1.5" role="tablist">
              <button
                type="button"
                onClick={() => setActiveCenterTab('visual')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeCenterTab === 'visual'
                    ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <Eye className="w-3.5 h-3.5" />
                Visual
              </button>

              <button
                type="button"
                onClick={() => setActiveCenterTab('columns')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeCenterTab === 'columns'
                    ? 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <Columns className="w-3.5 h-3.5" />
                Columns
                {state.plan && (
                  <span className="text-[10px] px-1 rounded bg-slate-800 text-slate-400 font-mono">
                    {state.plan.selected_columns?.length || 0}
                  </span>
                )}
              </button>

              <button
                type="button"
                onClick={() => setActiveCenterTab('filters')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeCenterTab === 'filters'
                    ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <Filter className="w-3.5 h-3.5" />
                Filters
                {state.plan && (state.plan.filters?.length || 0) > 0 && (
                  <span className="text-[10px] px-1 rounded bg-slate-800 text-amber-400 font-mono">
                    {state.plan.filters?.length || 0}
                  </span>
                )}
              </button>

              <button
                type="button"
                onClick={() => setActiveCenterTab('json')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeCenterTab === 'json'
                    ? 'bg-purple-500/15 text-purple-400 border border-purple-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <Code2 className="w-3.5 h-3.5" />
                JSON
              </button>

              <button
                type="button"
                onClick={() => setActiveCenterTab('history')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeCenterTab === 'history'
                    ? 'bg-slate-800 text-slate-100 border border-slate-700'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <History className="w-3.5 h-3.5" />
                History
                {(state.plan_versions?.length || 0) > 0 && (
                  <span className="text-[10px] px-1 rounded bg-slate-800 text-slate-400 font-mono">
                    {state.plan_versions.length}
                  </span>
                )}
              </button>
            </div>

            {state.plan && (
              <div className="text-xs font-mono text-slate-400">
                Target: <span className="text-emerald-400 font-bold">{state.plan.fact_view_name}</span>
              </div>
            )}
          </div>

          {/* Active Center Tab Content */}
          <div className="flex-1 overflow-hidden relative">
            {activeCenterTab === 'visual' && <VisualFlow />}
            {activeCenterTab === 'columns' && <ColumnsTable />}
            {activeCenterTab === 'filters' && <FiltersManager />}
            {activeCenterTab === 'json' && <JsonEditor />}
            {activeCenterTab === 'history' && <HistoryViewer />}
          </div>

          {/* Bottom Action Footer */}
          <ActionFooter />

        </main>

        {/* Right Column: Live Agent Timeline */}
        <LiveTimeline />

      </div>

      {/* Global Toast Notifications */}
      <ToastContainer />
    </div>
  );
};
