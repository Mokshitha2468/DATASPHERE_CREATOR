import React, { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { AgentLogEvent } from '../../types/logs';
import { Activity, Clock, ChevronDown, ChevronRight, AlertCircle, CheckCircle2, RotateCcw } from 'lucide-react';

export const LiveTimeline: React.FC = () => {
  const { agentEvents, state } = useAppStore();
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0);

  const events: AgentLogEvent[] = agentEvents.length > 0 ? agentEvents : (
    state.logs.map((log, idx): AgentLogEvent => ({
      type: 'log',
      agent: 'Orchestrator',
      step: log,
      status: log.toLowerCase().includes('error') ? 'failed' : 'completed',
      timestamp: Date.now() - (state.logs.length - idx) * 1000,
      iso_time: new Date().toISOString(),
      message: log,
    }))
  );

  return (
    <aside className="w-80 lg:w-96 bg-slate-900/70 border-l border-slate-800/80 p-4 flex flex-col h-[calc(100vh-61px)]">
      
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-sky-400 animate-pulse" />
          <h3 className="text-xs font-bold text-slate-100">Live Agent Timeline</h3>
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded-full font-mono bg-slate-800 text-sky-400 border border-slate-700">
          SSE Live
        </span>
      </div>

      {/* Events List */}
      <div className="flex-1 overflow-y-auto pt-3 space-y-2.5">
        {events.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs">
            <Clock className="w-6 h-6 mx-auto mb-2 text-slate-600" />
            Awaiting agent actions...
          </div>
        ) : (
          events.map((evt, idx) => {
            const isExpanded = expandedIndex === idx;
            const isError = evt.status === 'failed' || evt.type === 'agent_error';
            const isRetry = evt.step?.toLowerCase().includes('retry') || evt.step?.toLowerCase().includes('attempt 2');

            return (
              <div
                key={idx}
                className={`border rounded-xl p-2.5 text-xs transition-all ${
                  isError
                    ? 'bg-rose-500/10 border-rose-500/30 text-rose-200'
                    : isRetry
                    ? 'bg-amber-500/10 border-amber-500/30 text-amber-200'
                    : 'bg-slate-900/90 border-slate-800 text-slate-300 hover:border-slate-700'
                }`}
              >
                <div
                  onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                  className="flex items-start justify-between gap-2 cursor-pointer select-none"
                >
                  <div className="flex items-start gap-2 flex-1">
                    {isError ? (
                      <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                    ) : isRetry ? (
                      <RotateCcw className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    ) : (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    )}

                    <div className="flex-1">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="font-bold font-mono text-slate-200">{evt.agent || 'Orchestrator'}</span>
                        {isRetry && (
                          <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-amber-500/20 text-amber-300">
                            Retry
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400 mt-0.5 font-mono">{evt.step || evt.message}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5 text-[10px] text-slate-500 shrink-0 font-mono">
                    {evt.duration_ms && <span>{evt.duration_ms}ms</span>}
                    {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                  </div>
                </div>

                {/* Expanded Details Drawer */}
                {isExpanded && (evt.input || evt.output || evt.error) && (
                  <div className="mt-2 pt-2 border-t border-slate-800/80 space-y-1.5 font-mono text-[10px]">
                    {evt.input && (
                      <div>
                        <span className="text-slate-500 block font-bold">INPUT (Safe summary):</span>
                        <pre className="p-1.5 bg-slate-950 rounded text-slate-300 overflow-x-auto max-h-28">
                          {JSON.stringify(evt.input, null, 2)}
                        </pre>
                      </div>
                    )}

                    {evt.output && (
                      <div>
                        <span className="text-emerald-500 block font-bold">OUTPUT:</span>
                        <pre className="p-1.5 bg-slate-950 rounded text-emerald-300 overflow-x-auto max-h-32">
                          {typeof evt.output === 'object' ? JSON.stringify(evt.output, null, 2) : String(evt.output)}
                        </pre>
                      </div>
                    )}

                    {evt.error && (
                      <div>
                        <span className="text-rose-400 block font-bold">ERROR:</span>
                        <pre className="p-1.5 bg-rose-950/40 border border-rose-500/30 rounded text-rose-300 overflow-x-auto">
                          {evt.error}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

    </aside>
  );
};
