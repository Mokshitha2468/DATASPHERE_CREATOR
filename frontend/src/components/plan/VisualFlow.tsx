import React, { useMemo } from 'react';
import { useAppStore } from '../../store/useAppStore';
import {
  ReactFlow,
  Background,
  Controls,
  ReactFlowProvider,
  Node,
  Edge
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Database, Filter, Columns, Sparkles, AlertCircle } from 'lucide-react';

const VisualFlowInner: React.FC = () => {
  const { state } = useAppStore();
  const plan = state.plan;

  const selectedCount = plan?.selected_columns?.length || 0;
  const droppedCount = plan?.dropped_columns?.length || 0;
  const filterCount = plan?.filters?.length || 0;
  const unsupported = plan?.unsupported || [];

  // Hooks must be called unconditionally at the top of the component
  const nodes: Node[] = useMemo(() => {
    if (!plan) return [];
    return [
      {
        id: 'source-node',
        type: 'default',
        position: { x: 50, y: 150 },
        data: {
          label: (
            <div className="p-3 bg-slate-900 border border-sky-500/50 rounded-xl shadow-lg w-52 text-left select-none">
              <div className="flex items-center gap-2 text-sky-400 font-bold text-xs mb-1">
                <Database className="w-4 h-4" />
                <span>Source Table</span>
              </div>
              <div className="font-mono text-xs font-bold text-slate-100 truncate">{plan.source_table || 'SOURCE'}</div>
              <div className="text-[10px] text-slate-400 mt-1">{selectedCount + droppedCount} Total Columns</div>
            </div>
          ),
        },
        style: { background: 'transparent', border: 'none' },
      },
      {
        id: 'projection-node',
        type: 'default',
        position: { x: 300, y: 150 },
        data: {
          label: (
            <div className="p-3 bg-slate-900 border border-indigo-500/50 rounded-xl shadow-lg w-56 text-left select-none">
              <div className="flex items-center gap-2 text-indigo-400 font-bold text-xs mb-1">
                <Columns className="w-4 h-4" />
                <span>Projection (Columns)</span>
              </div>
              <div className="flex gap-2 text-[11px] font-mono mt-1.5">
                <span className="text-emerald-400 font-bold">{selectedCount} Kept</span>
                <span className="text-slate-500">•</span>
                <span className="text-slate-400">{droppedCount} Dropped</span>
              </div>
            </div>
          ),
        },
        style: { background: 'transparent', border: 'none' },
      },
      {
        id: 'filter-node',
        type: 'default',
        position: { x: 580, y: 150 },
        data: {
          label: (
            <div className="p-3 bg-slate-900 border border-amber-500/50 rounded-xl shadow-lg w-52 text-left select-none">
              <div className="flex items-center gap-2 text-amber-400 font-bold text-xs mb-1">
                <Filter className="w-4 h-4" />
                <span>Filter Logic</span>
              </div>
              <div className="text-xs font-mono text-slate-200 mt-1">
                {filterCount > 0 ? `${filterCount} Explicit Filter(s)` : 'No Filters'}
              </div>
            </div>
          ),
        },
        style: { background: 'transparent', border: 'none' },
      },
      {
        id: 'fact-node',
        type: 'default',
        position: { x: 840, y: 150 },
        data: {
          label: (
            <div className="p-3 bg-slate-900 border-2 border-emerald-500 rounded-xl shadow-xl shadow-emerald-500/10 w-64 text-left">
              <div className="flex items-center justify-between text-emerald-400 font-bold text-xs mb-1">
                <div className="flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4" />
                  <span>Fact View (Target)</span>
                </div>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 font-semibold">PLAN</span>
              </div>
              <div className="font-mono text-xs font-bold text-emerald-300 truncate mt-1">
                {plan.fact_view_name || 'FV_TARGET'}
              </div>
              <div className="text-[10px] text-slate-400 mt-1">Ready for Approval</div>
            </div>
          ),
        },
        style: { background: 'transparent', border: 'none' },
      },
    ];
  }, [plan, selectedCount, droppedCount, filterCount]);

  const edges: Edge[] = useMemo(() => {
    if (!plan) return [];
    return [
      {
        id: 'e-source-proj',
        source: 'source-node',
        target: 'projection-node',
        animated: true,
        style: { stroke: '#38bdf8', strokeWidth: 2 },
      },
      {
        id: 'e-proj-filter',
        source: 'projection-node',
        target: 'filter-node',
        animated: true,
        style: { stroke: '#818cf8', strokeWidth: 2 },
      },
      {
        id: 'e-filter-fact',
        source: 'filter-node',
        target: 'fact-node',
        animated: true,
        style: { stroke: '#34d399', strokeWidth: 2 },
      },
    ];
  }, [plan]);

  if (!plan) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center text-slate-500">
        <Sparkles className="w-10 h-10 text-slate-600 mb-3" />
        <h3 className="text-sm font-bold text-slate-300">No Plan Generated Yet</h3>
        <p className="text-xs max-w-sm mt-1">
          Provide your business requirement on the left and click "Generate Plan" to generate an automated modeling plan.
        </p>
      </div>
    );
  }

  return (
    <div className="h-full w-full min-h-[400px] bg-slate-950 relative">
      <div className="w-full h-full absolute inset-0">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          className="bg-[#080c14]"
        >
          <Background color="#1e293b" gap={20} size={1} />
          <Controls className="bg-slate-900 border border-slate-800 text-slate-300 rounded-lg" />
        </ReactFlow>
      </div>

      {/* Plan Summary Card Overlay */}
      <div className="absolute top-4 left-4 max-w-md bg-slate-900/90 backdrop-blur-md border border-slate-800 p-3.5 rounded-xl shadow-xl pointer-events-auto">
        <h4 className="text-xs font-bold text-slate-200 mb-1 flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-sky-400" />
          <span>Plan Summary</span>
        </h4>
        <p className="text-xs text-slate-400 leading-relaxed">{plan.summary || 'Plan generated successfully.'}</p>
        {unsupported.length > 0 && (
          <div className="mt-2 text-[11px] text-amber-400 bg-amber-500/10 border border-amber-500/20 p-2 rounded-lg flex items-start gap-1.5">
            <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            <div>
              <strong>Phase 2 Note:</strong> {unsupported.join(', ')}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export const VisualFlow: React.FC = () => {
  return (
    <ReactFlowProvider>
      <VisualFlowInner />
    </ReactFlowProvider>
  );
};
