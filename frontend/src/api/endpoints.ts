import { SharedState } from '../types/state';

const API_BASE = '/api';

export async function fetchState(): Promise<SharedState> {
  const res = await fetch(`${API_BASE}/state`);
  if (!res.ok) throw new Error('Failed to fetch state');
  return res.json();
}

export async function fetchSamples(): Promise<{ samples: { id: string; filename: string; label: string }[] }> {
  const res = await fetch(`${API_BASE}/samples`);
  if (!res.ok) throw new Error('Failed to fetch sample presets');
  return res.json();
}

export async function loadSampleContent(sampleId: string): Promise<{ filename: string; content: any }> {
  const res = await fetch(`${API_BASE}/samples/${sampleId}`);
  if (!res.ok) throw new Error('Failed to load sample content');
  return res.json();
}

export async function ingestSources(
  sourceFiles: File[],
  sampleFiles: File[],
  intention?: string,
  requirement?: string,
  rows: number = 20
): Promise<SharedState> {
  const formData = new FormData();
  sourceFiles.forEach(f => formData.append('files', f));
  sampleFiles.forEach(f => formData.append('sample_files', f));
  
  if (intention) formData.append('intention', intention);
  if (requirement) formData.append('requirement', requirement);
  formData.append('rows', rows.toString());

  const res = await fetch(`${API_BASE}/sources`, {
    method: 'POST',
    body: formData,
  });

  const data = await res.json();
  if (!res.ok || data.error) {
    throw new Error(data.error || 'Failed to ingest source metadata');
  }
  return data;
}

export async function generatePlan(requirement?: string, intention?: string): Promise<SharedState> {
  const res = await fetch(`${API_BASE}/plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ requirement, intention }),
  });
  const data = await res.json();
  if (!res.ok || data.error || data.detail) {
    throw new Error(data.detail || data.error || 'Failed to generate plan');
  }
  return data;
}

export async function editPlan(payload: { plan?: any; feedback?: string }): Promise<SharedState> {
  const res = await fetch(`${API_BASE}/plan/edit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok || data.error || data.detail) {
    throw new Error(data.detail || data.error || 'Failed to edit plan');
  }
  return data;
}

export async function approvePlan(): Promise<SharedState> {
  const res = await fetch(`${API_BASE}/plan/approve`, {
    method: 'POST',
  });
  const data = await res.json();
  if (!res.ok || data.error || data.detail) {
    throw new Error(data.detail || data.error || 'Failed to approve plan');
  }
  return data;
}

export async function resetState(): Promise<SharedState> {
  const res = await fetch(`${API_BASE}/state/reset`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to reset state');
  return res.json();
}
