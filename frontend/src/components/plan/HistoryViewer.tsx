import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import { History, GitCompare, Plus, Minus, ArrowRight, Sparkles } from 'lucide-react';

export const HistoryViewer: React.FC = () => {
  const { state, historyDiffVersions, setHistoryDiffVersions } = useAppStore();
  const versions = state.plan_versions || [];

  if (versions.length === 0) {
    return (
      <div className="p-8 text-center text-slate-500 text-xs">
        No version history available yet.
      </div>
    );
  }

  const [vA_num, vB_num] = historyDiffVersions;
  const versionA = versions.find(v => v.version === vA_num) || versions[0];
  const versionB = versions.find(v => v.version === vB_num) || versions[versions.length - 1];

  // Compute diff between versionA and versionB
  const planA = versionA?.plan;
  const planB = versionB?.plan;

  const keptA = new Set(planA?.selected_columns?.map(c => c.name) || []);
  const keptB = new Set(planB?.selected_columns?.map(c => c.name) || []);

  const columnsAdded = Array.from(keptB).filter(c => !keptA.has(c));
  const columnsRemoved = Array.from(keptA).filter(c => !keptB.has(c));
  const nameChanged = (planA?.fact_view_name || '') !== (planB?.fact_view_name || '');

  return (
    <div className="h-full overflow-auto p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <History className="w-4 h-4 text-indigo-400" />
            Plan Version History &amp; Diff
          </h3>
          <p className="text-xs text-slate-400">
            Compare snapshots across automated and user-edited plan iterations.
          </p>
        </div>

        {/* Version Pickers */}
        <div className="flex items-center gap-2 text-xs font-mono">
          <label className="text-slate-400">Base:</label>
          <select
            value={vA_num}
            onChange={(e) => setHistoryDiffVersions([parseInt(e.target.value, 10), vB_num])}
            className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200"
          >
            {versions.map(v => (
              <option key={v.version} value={v.version}>v{v.version} ({v.source})</option>
            ))}
          </select>

          <ArrowRight className="w-3.5 h-3.5 text-slate-500" />

          <label className="text-slate-400">Target:</label>
          <select
            value={vB_num}
            onChange={(e) => setHistoryDiffVersions([vA_num, parseInt(e.target.value, 10)])}
            className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200"
          >
            {versions.map(v => (
              <option key={v.version} value={v.version}>v{v.version} ({v.source})</option>
            ))}
          </select>
        </div>
      </div>

      {/* Diff Result Summary */}
      <div className="p-4 bg-slate-900/90 border border-slate-800 rounded-xl space-y-3">
        <h4 className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
          <GitCompare className="w-3.5 h-3.5 text-sky-400" />
          Diff: Plan v{versionA.version} → Plan v{versionB.version}
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
          {/* Columns Added */}
          <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg">
            <span className="text-[11px] font-bold text-emerald-400 flex items-center gap-1 mb-1.5">
              <Plus className="w-3.5 h-3.5" />
              Columns Added ({columnsAdded.length})
            </span>
            {columnsAdded.length === 0 ? (
              <span className="text-slate-600 italic">None</span>
            ) : (
              <div className="flex flex-wrap gap-1 font-mono">
                {columnsAdded.map(c => (
                  <span key={c} className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
                    +{c}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Columns Removed */}
          <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg">
            <span className="text-[11px] font-bold text-rose-400 flex items-center gap-1 mb-1.5">
              <Minus className="w-3.5 h-3.5" />
              Columns Removed ({columnsRemoved.length})
            </span>
            {columnsRemoved.length === 0 ? (
              <span className="text-slate-600 italic">None</span>
            ) : (
              <div className="flex flex-wrap gap-1 font-mono">
                {columnsRemoved.map(c => (
                  <span key={c} className="px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300">
                    -{c}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Fact View Name & Filters */}
          <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg">
            <span className="text-[11px] font-bold text-sky-400 flex items-center gap-1 mb-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              Entity Name &amp; Filters
            </span>
            {nameChanged ? (
              <div className="text-[11px] font-mono text-slate-300">
                Name: <span className="line-through text-slate-500">{planA.fact_view_name}</span> → <span className="text-emerald-400">{planB.fact_view_name}</span>
              </div>
            ) : (
              <div className="text-[11px] text-slate-500">Name unchanged ({planB.fact_view_name})</div>
            )}
            <div className="text-[11px] text-slate-400 mt-1">
              Filters: {planA.filters.length} in v{versionA.version} → {planB.filters.length} in v{versionB.version}
            </div>
          </div>
        </div>
      </div>

      {/* Version Timeline Cards */}
      <div className="space-y-2">
        <h4 className="text-xs font-semibold text-slate-400">All Version Snapshots ({versions.length})</h4>
        {versions.map((ver) => (
          <div
            key={ver.version}
            className={`p-3 rounded-xl border text-xs flex items-center justify-between ${
              ver.version === state.plan_version
                ? 'bg-slate-900 border-sky-500/50'
                : 'bg-slate-900/40 border-slate-800'
            }`}
          >
            <div className="flex items-center gap-3">
              <span className="px-2 py-1 rounded bg-slate-800 text-sky-400 font-mono font-bold">
                v{ver.version}
              </span>
              <div>
                <span className="font-bold text-slate-200">{ver.plan.fact_view_name}</span>
                <span className="text-slate-500 text-[11px] ml-2 font-mono">
                  ({ver.plan.selected_columns.length} kept, {ver.plan.dropped_columns.length} dropped, {ver.plan.filters.length} filters)
                </span>
              </div>
            </div>

            <div className="flex items-center gap-3 text-slate-400 text-[11px]">
              <span className="px-2 py-0.5 rounded bg-slate-800/80 text-slate-300 border border-slate-700">
                Source: {ver.source}
              </span>
              <span>{ver.created_at.slice(11, 19)} UTC</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
