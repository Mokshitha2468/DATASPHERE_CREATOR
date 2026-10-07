import React, { useState } from 'react';
import { SourceTable } from '../../types/source';
import { useAppStore } from '../../store/useAppStore';
import { Table, Eye, Database, X } from 'lucide-react';

interface SourceTableCardProps {
  table: SourceTable;
  index: number;
  isActive: boolean;
}

export const SourceTableCard: React.FC<SourceTableCardProps> = ({ table, index, isActive }) => {
  const { setActiveTableIndex, state } = useAppStore();
  const [showSyntheticModal, setShowSyntheticModal] = useState(false);

  const keys = table.fields.filter(f => f.is_key);
  const measures = table.fields.filter(f => f.inferred_classification === 'MEASURE_CANDIDATE' || f.explicit_aggregation);
  const dummyRows = state.dummy_data[table.name] || [];

  return (
    <>
      <div
        onClick={() => setActiveTableIndex(index)}
        className={`p-3 rounded-xl border transition-all cursor-pointer ${
          isActive
            ? 'bg-slate-800/90 border-sky-500 shadow-md shadow-sky-500/10'
            : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
        }`}
      >
        <div className="flex items-start justify-between gap-2 mb-1.5">
          <div>
            <div className="flex items-center gap-1.5">
              <Table className={`w-4 h-4 ${isActive ? 'text-sky-400' : 'text-slate-400'}`} />
              <h4 className="text-xs font-mono font-bold text-slate-100">{table.name}</h4>
            </div>
            {table.label && (
              <p className="text-[11px] text-slate-400 mt-0.5">{table.label}</p>
            )}
          </div>

          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowSyntheticModal(true);
            }}
            className="flex items-center gap-1 px-2 py-0.5 text-[10px] font-semibold bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 rounded transition-colors"
            title="Preview generated synthetic rows"
          >
            <Eye className="w-3 h-3" />
            20 Synthetic
          </button>
        </div>

        {/* Source connection & Remote Table chips */}
        <div className="flex flex-wrap gap-1 mb-2 text-[10px]">
          {table.source_connection && (
            <span className="px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 font-mono">
              Conn: {table.source_connection}
            </span>
          )}
          {table.remote_table && (
            <span className="px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-mono">
              Remote: {table.remote_table}
            </span>
          )}
        </div>

        {/* Metrics Bar */}
        <div className="grid grid-cols-3 gap-1 pt-1.5 border-t border-slate-800/80 text-[11px]">
          <div className="text-center">
            <span className="text-[10px] text-slate-500 block">Cols</span>
            <span className="font-mono font-bold text-slate-200">{table.fields.length}</span>
          </div>
          <div className="text-center">
            <span className="text-[10px] text-amber-500 block">Keys</span>
            <span className="font-mono font-bold text-amber-400">{keys.length}</span>
          </div>
          <div className="text-center">
            <span className="text-[10px] text-emerald-500 block">Measures</span>
            <span className="font-mono font-bold text-emerald-400">{measures.length}</span>
          </div>
        </div>
      </div>

      {/* Synthetic Rows Preview Modal */}
      {showSyntheticModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-5xl max-h-[85vh] flex flex-col shadow-2xl">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                  <Database className="w-4 h-4 text-sky-400" />
                  Generated Synthetic Rows for <span className="font-mono text-sky-400">{table.name}</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Safe synthetic data (20 rows) generated adhering to lengths, dates, precision, and unique keys.
                </p>
              </div>
              <button
                onClick={() => setShowSyntheticModal(false)}
                className="text-slate-400 hover:text-slate-200 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-4 overflow-auto flex-1">
              <table className="w-full text-left text-xs font-mono border-collapse">
                <thead>
                  <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400">
                    {table.fields.map(f => (
                      <th key={f.name} className="p-2.5 whitespace-nowrap">
                        {f.name} {f.is_key && '🔑'}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {dummyRows.map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-slate-800/40">
                      {table.fields.map(f => (
                        <td key={f.name} className="p-2.5 whitespace-nowrap">
                          {String(row[f.name] ?? '')}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="px-6 py-3 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setShowSyntheticModal(false)}
                className="px-4 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
