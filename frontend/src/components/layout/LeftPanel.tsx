import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import { SourceUpload } from '../source/SourceUpload';
import { SourceTableCard } from '../source/SourceTableCard';
import { RequirementsInput } from '../input/RequirementsInput';
import { Database } from 'lucide-react';

export const LeftPanel: React.FC = () => {
  const { state, activeTableIndex } = useAppStore();
  const tables = state.source_tables || [];

  return (
    <aside className="w-80 lg:w-96 bg-slate-900/70 border-r border-slate-800/80 p-4 flex flex-col gap-4 overflow-y-auto h-[calc(100vh-61px)]">
      
      {/* 1. Source Upload & Samples */}
      <SourceUpload />

      {/* 2. Ingested Source Tables */}
      {tables.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-sky-400" />
              Ingested Sources ({tables.length})
            </span>
          </div>

          <div className="space-y-2">
            {tables.map((table, idx) => (
              <SourceTableCard
                key={table.name}
                table={table}
                index={idx}
                isActive={idx === activeTableIndex}
              />
            ))}
          </div>
        </div>
      )}

      {/* 3. Intention, Requirements & Generate Action */}
      <RequirementsInput />

    </aside>
  );
};
