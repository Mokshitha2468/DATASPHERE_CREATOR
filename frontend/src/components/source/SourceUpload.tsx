import React, { useRef } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { FileCode, FileSpreadsheet, X, ShieldAlert, Sparkles } from 'lucide-react';
import * as api from '../../api/endpoints';

export const SourceUpload: React.FC = () => {
  const {
    sourceFiles,
    sampleFiles,
    addSourceFiles,
    removeSourceFile,
    addSampleFiles,
    removeSampleFile,
    ingestSourcesAction,
    isLoading,
    addToast
  } = useAppStore();

  const sourceInputRef = useRef<HTMLInputElement>(null);
  const sampleInputRef = useRef<HTMLInputElement>(null);

  const handleSourceDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.json'));
    if (files.length > 0) {
      addSourceFiles(files);
    } else {
      addToast('Please upload valid Datasphere JSON files.', 'error');
    }
  };

  const handleSampleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.csv') || f.name.endsWith('.json'));
    if (files.length > 0) {
      addSampleFiles(files);
      addToast(`Added ${files.length} sample file(s) for temporary pattern extraction.`, 'info');
    }
  };

  const handleQuickLoad = async (sampleId: string, filename: string) => {
    try {
      const data = await api.loadSampleContent(sampleId);
      const blob = new Blob([JSON.stringify(data.content, null, 2)], { type: 'application/json' });
      const file = new File([blob], filename, { type: 'application/json' });
      addSourceFiles([file]);
      addToast(`Loaded preset sample: ${filename}`, 'success');
    } catch (err: any) {
      addToast(err.message, 'error');
    }
  };

  return (
    <div className="space-y-4">
      
      {/* Quick Sample Presets */}
      <div>
        <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-2">
          Quick Load Presets:
        </span>
        <div className="flex flex-wrap gap-1.5">
          <button
            type="button"
            onClick={() => handleQuickLoad('sales_order_csn', 'sales_order_csn.json')}
            className="px-2 py-1 text-xs bg-slate-800/80 hover:bg-slate-800 text-slate-300 rounded border border-slate-700/80 transition-colors"
          >
            + Sales Orders CSN
          </button>
          <button
            type="button"
            onClick={() => handleQuickLoad('customer_remote_table', 'customer_remote_table.json')}
            className="px-2 py-1 text-xs bg-slate-800/80 hover:bg-slate-800 text-slate-300 rounded border border-slate-700/80 transition-colors"
          >
            + Customer Master
          </button>
          <button
            type="button"
            onClick={() => handleQuickLoad('multi_table_csn', 'multi_table_csn.json')}
            className="px-2 py-1 text-xs bg-slate-800/80 hover:bg-slate-800 text-slate-300 rounded border border-slate-700/80 transition-colors"
          >
            + Multi-Table CSN
          </button>
        </div>
      </div>

      {/* Source JSON Upload Dropzone */}
      <div>
        <label className="text-xs font-bold text-slate-300 block mb-1.5 flex items-center justify-between">
          <span>1. Datasphere Source JSON <span className="text-rose-400">*</span></span>
          <span className="text-[10px] text-slate-500 font-normal">CSN / Data Builder / Remote Table</span>
        </label>
        
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleSourceDrop}
          onClick={() => sourceInputRef.current?.click()}
          className="border-2 border-dashed border-sky-500/30 hover:border-sky-400 bg-slate-900/50 hover:bg-sky-500/5 rounded-xl p-3.5 text-center cursor-pointer transition-all group"
        >
          <input
            ref={sourceInputRef}
            type="file"
            multiple
            accept=".json"
            className="hidden"
            onChange={(e) => {
              if (e.target.files) addSourceFiles(Array.from(e.target.files));
              e.target.value = '';
            }}
          />
          <FileCode className="w-5 h-5 mx-auto text-sky-400 mb-1 group-hover:scale-110 transition-transform" />
          <p className="text-xs font-medium text-slate-200">
            Drop Source JSON or <span className="text-sky-400 underline">Browse</span>
          </p>
        </div>

        {/* Selected Source Files list */}
        {sourceFiles.length > 0 && (
          <div className="mt-2 space-y-1">
            {sourceFiles.map((file, idx) => (
              <div key={idx} className="flex items-center justify-between bg-slate-800/70 border border-slate-700 px-2.5 py-1 rounded text-xs">
                <span className="font-mono text-slate-300 truncate max-w-[200px]">{file.name}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); removeSourceFile(idx); }}
                  className="text-slate-500 hover:text-rose-400 p-0.5"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Optional Sample Data Upload */}
      <div className="pt-2 border-t border-slate-800/80">
        <label className="text-xs font-bold text-slate-300 block mb-1 flex items-center justify-between">
          <span className="flex items-center gap-1">
            <span>2. Sample Data</span>
            <span className="px-1.5 py-0.2 rounded text-[10px] font-semibold bg-slate-800 text-slate-400">OPTIONAL</span>
          </span>
          <span className="text-[10px] text-slate-500 font-normal">CSV / JSON (max 20 rows)</span>
        </label>

        {/* Privacy notice banner */}
        <div className="mb-2 p-2 rounded bg-emerald-500/10 border border-emerald-500/25 text-[11px] text-emerald-300 flex items-start gap-1.5">
          <ShieldAlert className="w-4 h-4 shrink-0 text-emerald-400 mt-0.5" />
          <div>
            <strong>Real Data Safety:</strong> Real rows are processed in memory to learn patterns, then <strong>immediately discarded</strong>. Only synthetic rows are sent to the Planner.
          </div>
        </div>

        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleSampleDrop}
          onClick={() => sampleInputRef.current?.click()}
          className="border border-dashed border-slate-700 hover:border-indigo-400 bg-slate-900/30 hover:bg-indigo-500/5 rounded-xl p-2.5 text-center cursor-pointer transition-all group"
        >
          <input
            ref={sampleInputRef}
            type="file"
            multiple
            accept=".csv,.json"
            className="hidden"
            onChange={(e) => {
              if (e.target.files) addSampleFiles(Array.from(e.target.files));
              e.target.value = '';
            }}
          />
          <FileSpreadsheet className="w-4 h-4 mx-auto text-indigo-400 mb-1 group-hover:scale-110 transition-transform" />
          <p className="text-[11px] text-slate-300">
            Attach Sample CSV/JSON (or continue without)
          </p>
        </div>

        {/* Selected Sample Files list */}
        {sampleFiles.length > 0 && (
          <div className="mt-2 space-y-1">
            {sampleFiles.map((file, idx) => (
              <div key={idx} className="flex items-center justify-between bg-slate-800/70 border border-slate-700 px-2.5 py-1 rounded text-xs">
                <span className="font-mono text-indigo-300 truncate max-w-[200px]">{file.name}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); removeSampleFile(idx); }}
                  className="text-slate-500 hover:text-rose-400 p-0.5"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Ingest Action Button */}
      {sourceFiles.length > 0 && (
        <button
          onClick={ingestSourcesAction}
          disabled={isLoading}
          className="w-full py-2 px-3 rounded-lg text-xs font-bold bg-sky-500 hover:bg-sky-400 text-slate-950 flex items-center justify-center gap-2 shadow-lg shadow-sky-500/20 transition-all disabled:opacity-50"
        >
          <Sparkles className="w-3.5 h-3.5" />
          {isLoading ? 'Ingesting & Generating Synthetic Rows...' : 'Ingest & Extract Metadata'}
        </button>
      )}

    </div>
  );
};
