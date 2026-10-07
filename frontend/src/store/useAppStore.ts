import { create } from 'zustand';
import { SharedState } from '../types/state';
import { AgentLogEvent } from '../types/logs';
import * as api from '../api/endpoints';

export interface ToastItem {
  id: string;
  text: string;
  type: 'success' | 'error' | 'info';
}

interface AppStore {
  state: SharedState;
  activeTableIndex: number;
  activeCenterTab: 'visual' | 'columns' | 'filters' | 'json' | 'history';
  sourceFiles: File[];
  sampleFiles: File[];
  intention: string;
  requirement: string;
  isLoading: boolean;
  error: string | null;
  agentEvents: AgentLogEvent[];
  toasts: ToastItem[];
  historyDiffVersions: [number, number];

  // Actions
  setSourceFiles: (files: File[]) => void;
  addSourceFiles: (files: File[]) => void;
  removeSourceFile: (index: number) => void;
  setSampleFiles: (files: File[]) => void;
  addSampleFiles: (files: File[]) => void;
  removeSampleFile: (index: number) => void;
  setIntention: (val: string) => void;
  setRequirement: (val: string) => void;
  setActiveTableIndex: (idx: number) => void;
  setActiveCenterTab: (tab: 'visual' | 'columns' | 'filters' | 'json' | 'history') => void;
  setHistoryDiffVersions: (versions: [number, number]) => void;
  addAgentEvent: (event: AgentLogEvent) => void;
  addToast: (text: string, type?: 'success' | 'error' | 'info') => void;
  removeToast: (id: string) => void;
  clearError: () => void;

  // Async API Actions
  loadInitialState: () => Promise<void>;
  ingestSourcesAction: () => Promise<void>;
  generatePlanAction: () => Promise<void>;
  editPlanAction: (plan: any) => Promise<void>;
  submitFeedbackAction: (feedback: string) => Promise<void>;
  approvePlanAction: () => Promise<void>;
  resetWorkspaceAction: () => Promise<void>;
}

const initialSharedState: SharedState = {
  intention: '',
  requirement: '',
  source_tables: [],
  dummy_data: {},
  plan: null,
  plan_version: 0,
  plan_versions: [],
  plan_status: 'draft',
  fact_view_name: '',
  stage: 'source',
  fact_view_json: null,
  graphical_view_json: null,
  analytical_model_json: null,
  llm_mode: 'MOCK',
  errors: [],
  logs: [],
};

export const useAppStore = create<AppStore>((set, get) => ({
  state: initialSharedState,
  activeTableIndex: 0,
  activeCenterTab: 'visual',
  sourceFiles: [],
  sampleFiles: [],
  intention: '',
  requirement: '',
  isLoading: false,
  error: null,
  agentEvents: [],
  toasts: [],
  historyDiffVersions: [1, 1],

  setSourceFiles: (files) => set({ sourceFiles: files }),
  addSourceFiles: (files) => set((s) => ({ sourceFiles: [...s.sourceFiles, ...files] })),
  removeSourceFile: (index) => set((s) => ({ sourceFiles: s.sourceFiles.filter((_, i) => i !== index) })),
  
  setSampleFiles: (files) => set({ sampleFiles: files }),
  addSampleFiles: (files) => set((s) => ({ sampleFiles: [...s.sampleFiles, ...files] })),
  removeSampleFile: (index) => set((s) => ({ sampleFiles: s.sampleFiles.filter((_, i) => i !== index) })),

  setIntention: (val) => set({ intention: val }),
  setRequirement: (val) => set({ requirement: val }),
  setActiveTableIndex: (idx) => set({ activeTableIndex: idx }),
  setActiveCenterTab: (tab) => set({ activeCenterTab: tab }),
  setHistoryDiffVersions: (versions) => set({ historyDiffVersions: versions }),

  addAgentEvent: (event) => set((s) => ({ agentEvents: [event, ...s.agentEvents].slice(0, 200) })),

  addToast: (text, type = 'info') => {
    const id = Math.random().toString(36).substring(2, 9);
    set((s) => ({ toasts: [...s.toasts, { id, text, type }] }));
    setTimeout(() => {
      get().removeToast(id);
    }, 4000);
  },

  removeToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
  clearError: () => set({ error: null }),

  loadInitialState: async () => {
    try {
      const data = await api.fetchState();
      set({
        state: data,
        intention: data.intention || '',
        requirement: data.requirement || '',
        historyDiffVersions: [Math.max(1, data.plan_version - 1), Math.max(1, data.plan_version)],
      });
    } catch (err: any) {
      console.warn('Could not load initial state:', err);
    }
  },

  ingestSourcesAction: async () => {
    const { sourceFiles, sampleFiles, intention, requirement, addToast } = get();
    if (sourceFiles.length === 0) {
      set({ error: 'Please upload at least one Datasphere JSON source file.' });
      return;
    }

    set({ isLoading: true, error: null });
    try {
      const data = await api.ingestSources(sourceFiles, sampleFiles, intention, requirement);
      set({
        state: data,
        activeTableIndex: 0,
        isLoading: false,
      });
      addToast(`Successfully ingested ${data.source_tables.length} source table(s).`, 'success');
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
      addToast(err.message, 'error');
    }
  },

  generatePlanAction: async () => {
    const { requirement, intention, addToast } = get();
    set({ isLoading: true, error: null });
    try {
      const data = await api.generatePlan(requirement, intention);
      set({
        state: data,
        activeCenterTab: 'visual',
        historyDiffVersions: [Math.max(1, data.plan_version - 1), data.plan_version],
        isLoading: false,
      });
      addToast(`Plan v${data.plan_version} generated successfully.`, 'success');
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
      addToast(err.message, 'error');
    }
  },

  editPlanAction: async (newPlan: any) => {
    const { addToast } = get();
    set({ isLoading: true, error: null });
    try {
      const data = await api.editPlan({ plan: newPlan });
      set({
        state: data,
        historyDiffVersions: [Math.max(1, data.plan_version - 1), data.plan_version],
        isLoading: false,
      });
      addToast(`Plan v${data.plan_version} updated. Marked as draft.`, 'success');
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
      addToast(err.message, 'error');
    }
  },

  submitFeedbackAction: async (feedback: string) => {
    const { addToast } = get();
    if (!feedback.trim()) return;
    set({ isLoading: true, error: null });
    try {
      const data = await api.editPlan({ feedback });
      set({
        state: data,
        historyDiffVersions: [Math.max(1, data.plan_version - 1), data.plan_version],
        isLoading: false,
      });
      addToast(`Re-planned to v${data.plan_version} based on feedback.`, 'success');
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
      addToast(err.message, 'error');
    }
  },

  approvePlanAction: async () => {
    const { addToast } = get();
    set({ isLoading: true, error: null });
    try {
      const data = await api.approvePlan();
      set({
        state: data,
        isLoading: false,
      });
      addToast('Plan approved! Fact Agent stub invoked.', 'success');
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
      addToast(err.message, 'error');
    }
  },

  resetWorkspaceAction: async () => {
    const { addToast } = get();
    set({ isLoading: true });
    try {
      const data = await api.resetState();
      set({
        state: data,
        sourceFiles: [],
        sampleFiles: [],
        intention: '',
        requirement: '',
        activeTableIndex: 0,
        isLoading: false,
        error: null,
      });
      addToast('Workspace state reset.', 'info');
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },
}));
