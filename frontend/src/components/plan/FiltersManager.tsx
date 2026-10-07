import React, { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { FilterSpec } from '../../types/plan';
import { Plus, Trash2 } from 'lucide-react';

const ALLOWED_OPS = [
  '=', '!=', '<>', '>', '>=', '<', '<=', 
  'BETWEEN', 'IN', 'NOT IN', 'LIKE', 'NOT LIKE', 
  'IS NULL', 'IS NOT NULL'
];

export const FiltersManager: React.FC = () => {
  const { state, editPlanAction } = useAppStore();
  const plan = state.plan;
  const sourceTable = state.source_tables.find(t => t.name === plan?.source_table) || state.source_tables[0];

  const [newCol, setNewCol] = useState(sourceTable?.fields[0]?.name || '');
  const [newOp, setNewOp] = useState('=');
  const [newVal, setNewVal] = useState('');
  const [newReason, setNewReason] = useState('');

  if (!plan || !sourceTable) {
    return (
      <div className="p-8 text-center text-slate-500 text-xs">
        No active plan available. Generate a plan first.
      </div>
    );
  }

  const handleAddFilter = () => {
    if (!newCol) return;
    const values = newVal.split(',').map(v => v.trim()).filter(Boolean);
    const newFilter: FilterSpec = {
      column: newCol,
      operator: newOp,
      values: values.length > 0 ? values : [newVal],
      reason: newReason || 'User defined filter constraint.',
    };

    editPlanAction({
      ...plan,
      filters: [...plan.filters, newFilter],
    });

    setNewVal('');
    setNewReason('');
  };

  const handleDeleteFilter = (index: number) => {
    const updated = plan.filters.filter((_, i) => i !== index);
    editPlanAction({
      ...plan,
      filters: updated,
    });
  };

  return (
    <div className="h-full overflow-auto p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-100">Plan Filter Expressions</h3>
          <p className="text-xs text-slate-400">
            Define explicit data filters. Only allowed filter operators for Datasphere are permitted.
          </p>
        </div>
      </div>

      {/* Add Filter Box */}
      <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl space-y-3">
        <h4 className="text-xs font-bold text-sky-400 flex items-center gap-1.5">
          <Plus className="w-3.5 h-3.5" />
          Add Filter Constraint
        </h4>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-2 text-xs">
          {/* Column selector */}
          <div>
            <label className="text-[11px] text-slate-400 block mb-1">Column</label>
            <select
              value={newCol}
              onChange={(e) => setNewCol(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 font-mono focus:outline-none focus:border-sky-400"
            >
              {sourceTable.fields.map(f => (
                <option key={f.name} value={f.name}>{f.name}</option>
              ))}
            </select>
          </div>

          {/* Operator selector */}
          <div>
            <label className="text-[11px] text-slate-400 block mb-1">Operator</label>
            <select
              value={newOp}
              onChange={(e) => setNewOp(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 font-mono focus:outline-none focus:border-sky-400"
            >
              {ALLOWED_OPS.map(op => (
                <option key={op} value={op}>{op}</option>
              ))}
            </select>
          </div>

          {/* Value input */}
          <div>
            <label className="text-[11px] text-slate-400 block mb-1">Value(s)</label>
            <input
              type="text"
              value={newVal}
              onChange={(e) => setNewVal(e.target.value)}
              placeholder="e.g. ACTIVE or 100, 200"
              className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-sky-400"
            />
          </div>

          {/* Reason input & Add CTA */}
          <div>
            <label className="text-[11px] text-slate-400 block mb-1">Reason</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={newReason}
                onChange={(e) => setNewReason(e.target.value)}
                placeholder="Reason..."
                className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-sky-400"
              />
              <button
                type="button"
                onClick={handleAddFilter}
                className="px-3 py-1.5 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold rounded shrink-0 transition-colors"
              >
                Add
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Active Filters List */}
      <div className="space-y-2">
        <h4 className="text-xs font-semibold text-slate-300">Active Filters ({plan.filters.length})</h4>

        {plan.filters.length === 0 ? (
          <div className="p-6 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl text-xs">
            No filters currently applied to this plan.
          </div>
        ) : (
          plan.filters.map((filter, idx) => (
            <div
              key={idx}
              className="p-3 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between gap-4 text-xs font-mono"
            >
              <div className="flex items-center gap-3">
                <span className="w-6 h-6 rounded-full bg-amber-500/15 text-amber-400 flex items-center justify-center text-[10px] font-bold">
                  {idx + 1}
                </span>
                <span className="font-bold text-slate-200">{filter.column}</span>
                <span className="px-2 py-0.5 rounded bg-slate-800 text-amber-400 font-bold border border-slate-700">
                  {filter.operator}
                </span>
                <span className="text-emerald-400 font-semibold">
                  {JSON.stringify(filter.values)}
                </span>
              </div>

              <div className="flex items-center gap-3 font-sans">
                <span className="text-slate-400 text-xs italic">{filter.reason}</span>
                <button
                  onClick={() => handleDeleteFilter(idx)}
                  className="p-1.5 text-slate-500 hover:text-rose-400 rounded transition-colors"
                  title="Remove filter"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
