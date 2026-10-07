import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import { Sparkles, MessageSquare, Target } from 'lucide-react';

export const RequirementsInput: React.FC = () => {
  const {
    intention,
    requirement,
    setIntention,
    setRequirement,
    generatePlanAction,
    state,
    isLoading
  } = useAppStore();

  const hasSources = state.source_tables.length > 0;

  return (
    <div className="space-y-3 pt-3 border-t border-slate-800">
      <div>
        <label className="text-xs font-bold text-slate-300 block mb-1 flex items-center gap-1.5">
          <Target className="w-3.5 h-3.5 text-indigo-400" />
          <span>User Intention</span>
        </label>
        <input
          type="text"
          value={intention}
          onChange={(e) => setIntention(e.target.value)}
          placeholder="e.g. Sales Revenue Analytics Fact View"
          className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-400"
        />
      </div>

      <div>
        <label className="text-xs font-bold text-slate-300 block mb-1 flex items-center gap-1.5">
          <MessageSquare className="w-3.5 h-3.5 text-sky-400" />
          <span>Business Requirement</span>
        </label>
        <textarea
          value={requirement}
          onChange={(e) => setRequirement(e.target.value)}
          rows={3}
          placeholder="e.g. Calculate net revenue by customer country and order date. Exclude cancelled orders."
          className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-400 resize-none"
        />
      </div>

      <button
        type="button"
        onClick={generatePlanAction}
        disabled={isLoading || !hasSources}
        className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold flex items-center justify-center gap-2 shadow-lg transition-all ${
          hasSources && !isLoading
            ? 'bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white shadow-sky-500/25 cursor-pointer'
            : 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50'
        }`}
      >
        <Sparkles className="w-4 h-4" />
        {isLoading ? 'Generating Plan...' : state.plan ? 'Re-Generate Plan' : 'Generate Plan (Phase 2)'}
      </button>

      {!hasSources && (
        <p className="text-[10px] text-center text-slate-500">
          Upload and ingest at least one source table above to generate a plan.
        </p>
      )}
    </div>
  );
};
