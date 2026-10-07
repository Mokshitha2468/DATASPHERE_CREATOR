import React, { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { CheckCircle, Send, RotateCcw } from 'lucide-react';

export const ActionFooter: React.FC = () => {
  const { state, approvePlanAction, submitFeedbackAction, generatePlanAction, isLoading } = useAppStore();
  const [feedbackText, setFeedbackText] = useState('');

  const plan = state.plan;
  const isApproved = state.plan_status === 'approved';

  if (!plan) return null;

  const handleFeedbackSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!feedbackText.trim()) return;
    submitFeedbackAction(feedbackText);
    setFeedbackText('');
  };

  return (
    <footer className="border-t border-slate-800/80 bg-slate-900/90 backdrop-blur-md px-6 py-3 flex items-center justify-between flex-wrap gap-4">
      
      {/* Feedback input box */}
      <form onSubmit={handleFeedbackSubmit} className="flex-1 max-w-xl flex items-center gap-2">
        <div className="relative flex-1">
          <input
            type="text"
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            disabled={isLoading}
            placeholder="Give feedback (e.g. 'Drop CUSTOMER_ID and filter where AMOUNT > 500')..."
            className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-3 pr-8 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-400"
          />
        </div>
        <button
          type="submit"
          disabled={isLoading || !feedbackText.trim()}
          className="px-3 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 transition-colors shadow-md shadow-indigo-600/20"
        >
          <Send className="w-3.5 h-3.5" />
          Re-Plan
        </button>
      </form>

      {/* Approve & Reset Actions */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={generatePlanAction}
          disabled={isLoading}
          className="px-3 py-2 text-xs font-semibold text-slate-400 hover:text-slate-200 bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition-colors flex items-center gap-1.5"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Reset Plan
        </button>

        <button
          type="button"
          onClick={approvePlanAction}
          disabled={isLoading || isApproved}
          className={`px-5 py-2 rounded-lg text-xs font-bold flex items-center gap-2 transition-all shadow-lg ${
            isApproved
              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 cursor-default'
              : 'bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-emerald-500/20 cursor-pointer'
          }`}
        >
          <CheckCircle className="w-4 h-4" />
          {isApproved ? 'Plan Approved ✓' : 'Approve Plan (Lock Spec)'}
        </button>
      </div>

    </footer>
  );
};
