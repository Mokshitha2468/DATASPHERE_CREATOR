import React, { useState, useEffect } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { Copy, Check, Save, AlertCircle, Edit3 } from 'lucide-react';

export const JsonEditor: React.FC = () => {
  const { state, editPlanAction, addToast } = useAppStore();
  const plan = state.plan;

  const [isEditing, setIsEditing] = useState(false);
  const [jsonText, setJsonText] = useState('');
  const [parseError, setParseError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (plan) {
      setJsonText(JSON.stringify(plan, null, 2));
      setParseError(null);
    }
  }, [plan]);

  if (!plan) {
    return (
      <div className="p-8 text-center text-slate-500 text-xs">
        No active plan available. Generate a plan first.
      </div>
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonText);
    setCopied(true);
    addToast('Plan JSON copied to clipboard!', 'info');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSave = () => {
    try {
      const parsed = JSON.parse(jsonText);
      setParseError(null);
      editPlanAction(parsed);
      setIsEditing(false);
    } catch (err: any) {
      setParseError(`JSON Syntax Error: ${err.message}`);
    }
  };

  return (
    <div className="h-full flex flex-col p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-100">Structured PlanSpec JSON</h3>
          <p className="text-xs text-slate-400">
            Validated schema passed to downstream code generation phases.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? 'Copied' : 'Copy JSON'}
          </button>

          {isEditing ? (
            <button
              onClick={handleSave}
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-bold bg-sky-500 hover:bg-sky-400 text-slate-950 rounded-lg transition-colors shadow-md shadow-sky-500/20"
            >
              <Save className="w-3.5 h-3.5" />
              Save Changes
            </button>
          ) : (
            <button
              onClick={() => setIsEditing(true)}
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-semibold bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-500/30 rounded-lg transition-colors"
            >
              <Edit3 className="w-3.5 h-3.5" />
              Edit JSON
            </button>
          )}
        </div>
      </div>

      {parseError && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{parseError}</span>
        </div>
      )}

      <div className="flex-1 border border-slate-800 rounded-xl overflow-hidden relative">
        {isEditing ? (
          <textarea
            value={jsonText}
            onChange={(e) => {
              setJsonText(e.target.value);
              try {
                JSON.parse(e.target.value);
                setParseError(null);
              } catch (err: any) {
                setParseError(err.message);
              }
            }}
            className="w-full h-full bg-[#050811] text-sky-300 font-mono text-xs p-4 focus:outline-none resize-none"
            spellCheck={false}
          />
        ) : (
          <pre className="w-full h-full bg-[#050811] text-sky-300 font-mono text-xs p-4 overflow-auto">
            <code>{jsonText}</code>
          </pre>
        )}
      </div>
    </div>
  );
};
