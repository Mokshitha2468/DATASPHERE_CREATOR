import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import { PlanSpec, ColumnDecision } from '../../types/plan';
import { Check, X, Key } from 'lucide-react';

export const ColumnsTable: React.FC = () => {
  const { state, editPlanAction } = useAppStore();
  const plan = state.plan;
  const sourceTable = state.source_tables.find(t => t.name === plan?.source_table) || state.source_tables[0];

  if (!plan || !sourceTable) {
    return (
      <div className="p-8 text-center text-slate-500 text-xs">
        No active plan available. Generate a plan first.
      </div>
    );
  }

  const selectedMap = new Map<string, ColumnDecision>();
  plan.selected_columns.forEach(c => selectedMap.set(c.name, c));

  const droppedMap = new Map<string, ColumnDecision>();
  plan.dropped_columns.forEach(c => droppedMap.set(c.name, c));

  const toggleColumnDecision = (colName: string, currentlyKept: boolean) => {
    let newSelected = [...plan.selected_columns];
    let newDropped = [...plan.dropped_columns];

    if (currentlyKept) {
      // Switch from keep to drop
      newSelected = newSelected.filter(c => c.name !== colName);
      newDropped.push({
        name: colName,
        reason: 'Manually excluded by user in column editor.',
      });
    } else {
      // Switch from drop to keep
      newDropped = newDropped.filter(c => c.name !== colName);
      newSelected.push({
        name: colName,
        reason: 'Manually included by user in column editor.',
      });
    }

    const updatedPlan: PlanSpec = {
      ...plan,
      selected_columns: newSelected,
      dropped_columns: newDropped,
    };
    editPlanAction(updatedPlan);
  };

  const handleReasonChange = (colName: string, isKept: boolean, newReason: string) => {
    let newSelected = [...plan.selected_columns];
    let newDropped = [...plan.dropped_columns];

    if (isKept) {
      newSelected = newSelected.map(c => c.name === colName ? { ...c, reason: newReason } : c);
    } else {
      newDropped = newDropped.map(c => c.name === colName ? { ...c, reason: newReason } : c);
    }

    editPlanAction({
      ...plan,
      selected_columns: newSelected,
      dropped_columns: newDropped,
    });
  };

  return (
    <div className="h-full overflow-auto p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-100">Column Projection Decisions</h3>
          <p className="text-xs text-slate-400">
            Keep or drop source columns. Manual toggles update plan status to <span className="text-sky-400 font-semibold">DRAFT</span>.
          </p>
        </div>
        <div className="flex gap-3 text-xs font-mono">
          <span className="text-emerald-400 font-bold">{plan.selected_columns.length} Kept</span>
          <span className="text-rose-400 font-bold">{plan.dropped_columns.length} Dropped</span>
        </div>
      </div>

      <div className="border border-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-900 border-b border-slate-800 text-slate-400 font-bold">
              <th className="p-3 w-28">Decision</th>
              <th className="p-3">Column</th>
              <th className="p-3">Label</th>
              <th className="p-3">Type</th>
              <th className="p-3">Classification</th>
              <th className="p-3">Reason / Justification</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 bg-slate-950/50">
            {sourceTable.fields.map(field => {
              const isKept = selectedMap.has(field.name);
              const decision = isKept ? selectedMap.get(field.name) : droppedMap.get(field.name);

              return (
                <tr key={field.name} className="hover:bg-slate-900/40 transition-colors">
                  {/* Toggle Button */}
                  <td className="p-3">
                    <button
                      type="button"
                      onClick={() => toggleColumnDecision(field.name, isKept)}
                      className={`px-3 py-1 rounded-full font-bold text-[11px] flex items-center gap-1.5 transition-colors ${
                        isKept
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 hover:bg-emerald-500/30'
                          : 'bg-rose-500/15 text-rose-400 border border-rose-500/30 hover:bg-rose-500/25'
                      }`}
                    >
                      {isKept ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
                      {isKept ? 'KEEP' : 'DROP'}
                    </button>
                  </td>

                  {/* Column Name */}
                  <td className="p-3 font-mono font-semibold text-slate-200">
                    <div className="flex items-center gap-1.5">
                      <span>{field.name}</span>
                      {field.is_key && (
                        <span className="px-1 py-0.2 rounded text-[10px] bg-amber-500/20 text-amber-400 font-sans font-bold flex items-center gap-0.5">
                          <Key className="w-2.5 h-2.5" /> KEY
                        </span>
                      )}
                    </div>
                  </td>

                  {/* Label */}
                  <td className="p-3 text-slate-400 truncate max-w-[140px]">
                    {field.label || '-'}
                  </td>

                  {/* Data Type */}
                  <td className="p-3 font-mono text-[11px] text-sky-400">
                    {field.data_type}
                  </td>

                  {/* Classification */}
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
                      {field.inferred_classification}
                    </span>
                  </td>

                  {/* Reason (Editable input) */}
                  <td className="p-3">
                    <input
                      type="text"
                      value={decision?.reason || ''}
                      onChange={(e) => handleReasonChange(field.name, isKept, e.target.value)}
                      placeholder="Explain reasoning..."
                      className="w-full bg-slate-900/80 border border-slate-800 focus:border-slate-600 rounded px-2 py-1 text-xs text-slate-300 focus:outline-none"
                    />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
