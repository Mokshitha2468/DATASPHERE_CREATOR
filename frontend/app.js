/**
 * Datasphere Creator - Frontend Logic (Phase 1).
 */

document.addEventListener('DOMContentLoaded', () => {
  // Application State
  const appState = {
    selectedFiles: [],
    loadedSharedState: null,
    activeTableIndex: 0,
    activeView: 'schema', // 'schema', 'dummy', 'llm'
  };

  // DOM Elements
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');
  const browseBtn = document.getElementById('browse-btn');
  const fileChipsWrapper = document.getElementById('file-chips');
  const sampleButtonsContainer = document.getElementById('sample-buttons');
  const requirementInput = document.getElementById('requirement-input');
  const rowsInput = document.getElementById('rows-input');
  const processBtn = document.getElementById('process-btn');
  const loadingState = document.getElementById('loading-state');
  const errorBanner = document.getElementById('error-banner');
  const errorMessage = document.getElementById('error-message');
  const closeErrorBtn = document.getElementById('close-error-btn');
  const resultsArea = document.getElementById('results-area');

  // Metrics
  const metricTables = document.getElementById('metric-tables');
  const metricFields = document.getElementById('metric-fields');
  const metricKeys = document.getElementById('metric-keys');
  const metricMeasures = document.getElementById('metric-measures');
  const metricDummy = document.getElementById('metric-dummy');

  // Table Tabs & View
  const tableTabList = document.getElementById('table-tab-list');
  const currentTableName = document.getElementById('current-table-name');
  const currentTableLabel = document.getElementById('current-table-label');
  const currentTableChips = document.getElementById('current-table-chips');
  const schemaTableBody = document.getElementById('schema-table-body');
  const dummyTableHead = document.getElementById('dummy-table-head');
  const dummyTableBody = document.getElementById('dummy-table-body');
  const llmJsonContent = document.getElementById('llm-json-content');
  const logCountSpan = document.getElementById('log-count');

  // Switchers & Modals
  const viewTabs = document.querySelectorAll('.view-tab');
  const viewPanels = {
    schema: document.getElementById('view-schema-container'),
    dummy: document.getElementById('view-dummy-container'),
    llm: document.getElementById('view-llm-container'),
  };

  const stateModal = document.getElementById('state-modal');
  const logsModal = document.getElementById('logs-modal');
  const sharedStateJson = document.getElementById('shared-state-json');
  const logList = document.getElementById('log-list');

  // Initialize
  init();

  async function init() {
    setupEventListeners();
    await loadSamplePresets();
  }

  function setupEventListeners() {
    // Dropzone & File Input
    browseBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.click();
    });

    dropzone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
      handleFiles(Array.from(e.target.files));
      fileInput.value = '';
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('dragover');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = Array.from(dt.files).filter(f => f.name.endsWith('.json') || f.type.includes('json'));
      if (files.length > 0) {
        handleFiles(files);
      } else {
        showError('Please upload valid .json files.');
      }
    });

    // Pipeline Execution
    processBtn.addEventListener('click', executePipeline);

    // Close error
    closeErrorBtn.addEventListener('click', () => {
      errorBanner.classList.add('hidden');
    });

    // View Switchers
    viewTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const view = tab.getAttribute('data-view');
        switchView(view);
      });
    });

    // Modals
    document.getElementById('view-shared-state-btn').addEventListener('click', () => {
      if (!appState.loadedSharedState) return;
      sharedStateJson.textContent = JSON.stringify(appState.loadedSharedState, null, 2);
      stateModal.showModal();
    });

    document.getElementById('close-modal-btn').addEventListener('click', () => stateModal.close());
    document.getElementById('dismiss-modal-btn').addEventListener('click', () => stateModal.close());

    document.getElementById('view-logs-btn').addEventListener('click', () => {
      if (!appState.loadedSharedState) return;
      renderLogs(appState.loadedSharedState.logs || [], appState.loadedSharedState.errors || []);
      logsModal.showModal();
    });

    document.getElementById('close-logs-btn').addEventListener('click', () => logsModal.close());
    document.getElementById('dismiss-logs-btn').addEventListener('click', () => logsModal.close());

    // Copy Buttons
    document.getElementById('copy-state-btn').addEventListener('click', () => {
      copyToClipboard(sharedStateJson.textContent, 'State JSON copied to clipboard!');
    });

    document.getElementById('copy-llm-btn').addEventListener('click', () => {
      copyToClipboard(llmJsonContent.textContent, 'LLM summary copied!');
    });

    document.getElementById('copy-dummy-json-btn').addEventListener('click', () => {
      if (!appState.loadedSharedState) return;
      const table = appState.loadedSharedState.source_tables[appState.activeTableIndex];
      if (table) {
        const rows = appState.loadedSharedState.dummy_data[table.name] || [];
        copyToClipboard(JSON.stringify(rows, null, 2), `20 synthetic rows for '${table.name}' copied!`);
      }
    });
  }

  function handleFiles(files) {
    for (const f of files) {
      if (!appState.selectedFiles.some(existing => existing.name === f.name && existing.size === f.size)) {
        appState.selectedFiles.push(f);
      }
    }
    renderFileChips();
  }

  function renderFileChips() {
    fileChipsWrapper.innerHTML = '';
    appState.selectedFiles.forEach((file, idx) => {
      const chip = document.createElement('div');
      chip.className = 'file-chip';
      chip.innerHTML = `
        <span>📄 ${escapeHtml(file.name)}</span>
        <button type="button" class="remove-file" title="Remove file" data-index="${idx}">✕</button>
      `;
      chip.querySelector('.remove-file').addEventListener('click', (e) => {
        e.stopPropagation();
        const removeIdx = parseInt(e.target.getAttribute('data-index'), 10);
        appState.selectedFiles.splice(removeIdx, 1);
        renderFileChips();
      });
      fileChipsWrapper.appendChild(chip);
    });
  }

  async function loadSamplePresets() {
    try {
      const res = await fetch('/api/samples');
      const data = await res.json();
      sampleButtonsContainer.innerHTML = '';
      
      data.samples.forEach(sample => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-outline btn-xs';
        btn.textContent = `+ ${sample.label}`;
        btn.addEventListener('click', async () => {
          await addSampleFile(sample.id, sample.filename);
        });
        sampleButtonsContainer.appendChild(btn);
      });
    } catch (e) {
      console.warn('Could not load sample presets:', e);
    }
  }

  async function addSampleFile(sampleId, filename) {
    try {
      const res = await fetch(`/api/samples/${sampleId}`);
      const data = await res.json();
      const blob = new Blob([JSON.stringify(data.content, null, 2)], { type: 'application/json' });
      const file = new File([blob], filename, { type: 'application/json' });
      handleFiles([file]);
    } catch (e) {
      showError(`Failed to load sample: ${e.message}`);
    }
  }

  async function executePipeline() {
    if (appState.selectedFiles.length === 0) {
      showError('Please select or drag-and-drop at least one Datasphere JSON source file.');
      return;
    }

    hideError();
    loadingState.classList.remove('hidden');
    resultsArea.classList.add('hidden');

    const formData = new FormData();
    appState.selectedFiles.forEach(f => formData.append('files', f));

    const reqText = requirementInput.value.trim();
    if (reqText) formData.append('requirement', reqText);

    const rowsCount = parseInt(rowsInput.value, 10) || 20;
    formData.append('rows', rowsCount.toString());

    try {
      const res = await fetch('/api/process', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (!res.ok || data.error) {
        throw new Error(data.error || 'Failed to process source files.');
      }

      appState.loadedSharedState = data;
      appState.activeTableIndex = 0;
      renderResults(data);
    } catch (err) {
      showError(err.message);
    } finally {
      loadingState.classList.add('hidden');
    }
  }

  function renderResults(state) {
    resultsArea.classList.remove('hidden');

    const tables = state.source_tables || [];
    let totalFields = 0;
    let totalKeys = 0;
    let totalMeasures = 0;
    let totalDummyRows = 0;

    tables.forEach(t => {
      totalFields += (t.fields || []).length;
      totalKeys += (t.fields || []).filter(f => f.is_key).length;
      totalMeasures += (t.fields || []).filter(f => 
        f.inferred_classification === 'MEASURE_CANDIDATE' || f.explicit_aggregation
      ).length;
      const rows = state.dummy_data[t.name] || [];
      totalDummyRows += rows.length;
    });

    metricTables.textContent = tables.length.toString();
    metricFields.textContent = totalFields.toString();
    metricKeys.textContent = totalKeys.toString();
    metricMeasures.textContent = totalMeasures.toString();
    metricDummy.textContent = totalDummyRows.toString();
    logCountSpan.textContent = (state.logs || []).length.toString();

    renderTableTabs(tables);
    renderActiveTable();
  }

  function renderTableTabs(tables) {
    tableTabList.innerHTML = '';
    tables.forEach((t, idx) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = `tab-pill ${idx === appState.activeTableIndex ? 'active' : ''}`;
      btn.innerHTML = `
        <span>${escapeHtml(t.name)}</span>
        <span class="tab-badge">${(t.fields || []).length} cols</span>
      `;
      btn.addEventListener('click', () => {
        appState.activeTableIndex = idx;
        document.querySelectorAll('.tab-pill').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        renderActiveTable();
      });
      tableTabList.appendChild(btn);
    });
  }

  function renderActiveTable() {
    const state = appState.loadedSharedState;
    if (!state || !state.source_tables || state.source_tables.length === 0) return;

    const table = state.source_tables[appState.activeTableIndex] || state.source_tables[0];
    
    // Header Info
    currentTableName.textContent = table.name;
    currentTableLabel.textContent = table.label || 'No description label provided';

    // Meta chips
    currentTableChips.innerHTML = '';
    if (table.source_connection) {
      currentTableChips.appendChild(createChip('Conn:', table.source_connection, 'badge-info'));
    }
    if (table.remote_table) {
      currentTableChips.appendChild(createChip('Remote Table:', table.remote_table, 'badge-neutral'));
    }
    if (table.modeling_metadata && table.modeling_metadata.dataCategory) {
      currentTableChips.appendChild(createChip('Category:', table.modeling_metadata.dataCategory, 'badge-measure'));
    }
    if (table.capabilities && table.capabilities.length > 0) {
      currentTableChips.appendChild(createChip('Capabilities:', table.capabilities.join(', '), 'badge-flag'));
    }
    if (table.filters && table.filters.length > 0) {
      currentTableChips.appendChild(createChip('Filter:', JSON.stringify(table.filters), 'badge-agg'));
    }

    // Render View 1: Schema Table
    renderSchemaView(table);

    // Render View 2: Dummy Data Grid
    renderDummyDataView(table, state.dummy_data[table.name] || []);

    // Render View 3: LLM Summary
    renderLlmSummaryView(table);
  }

  function renderSchemaView(table) {
    schemaTableBody.innerHTML = '';
    const fields = table.fields || [];

    fields.forEach(field => {
      const tr = document.createElement('tr');

      // Key icon
      const keyCol = field.is_key 
        ? `<span class="badge badge-key">🔑 KEY</span>` 
        : `<span style="color: var(--text-muted);">-</span>`;

      // Dimensions & Measures badges
      let classBadge = `<span class="badge badge-neutral">${field.inferred_classification}</span>`;
      if (field.inferred_classification === 'MEASURE_CANDIDATE') {
        classBadge = `<span class="badge badge-measure">MEASURE CANDIDATE</span>`;
      } else if (field.inferred_classification === 'DIMENSION_CANDIDATE') {
        classBadge = `<span class="badge badge-dimension">DIMENSION</span>`;
      } else if (field.inferred_classification === 'KEY_IDENTIFIER') {
        classBadge = `<span class="badge badge-key">KEY IDENTIFIER</span>`;
      } else if (field.inferred_classification === 'DATE_TIME') {
        classBadge = `<span class="badge badge-date">DATE / TIME</span>`;
      } else if (field.inferred_classification === 'BOOLEAN_FLAG') {
        classBadge = `<span class="badge badge-flag">BOOLEAN</span>`;
      }

      // Explicit Aggregation
      const aggBadge = field.explicit_aggregation
        ? `<span class="badge badge-agg">${escapeHtml(field.explicit_aggregation)}</span>`
        : `<span style="color: var(--text-muted);">None</span>`;

      // Length / Precision / Scale
      let dimDetails = [];
      if (field.length !== null && field.length !== undefined) dimDetails.push(`L:${field.length}`);
      if (field.precision !== null && field.precision !== undefined) dimDetails.push(`P:${field.precision}`);
      if (field.scale !== null && field.scale !== undefined) dimDetails.push(`S:${field.scale}`);
      const dimStr = dimDetails.length > 0 ? dimDetails.join(' / ') : '-';

      // Nullable / Filterable
      const nullStr = field.is_nullable ? 'Nullable' : '<strong>NOT NULL</strong>';
      const filtStr = field.is_filterable ? 'Filterable' : 'No-Filter';

      // Annotation count
      const annotCount = Object.keys(field.annotations || {}).length + Object.keys(field.additional_metadata || {}).length;
      const metaStr = annotCount > 0 ? `<span class="badge badge-neutral">${annotCount} attrs</span>` : '-';

      tr.innerHTML = `
        <td>${keyCol}</td>
        <td class="mono-col">${escapeHtml(field.name)}</td>
        <td>${escapeHtml(field.label || '-')}</td>
        <td><code>${escapeHtml(field.data_type)}</code></td>
        <td>${dimStr}</td>
        <td><small>${nullStr} • ${filtStr}</small></td>
        <td>${aggBadge}</td>
        <td>${classBadge}</td>
        <td>${metaStr}</td>
      `;

      schemaTableBody.appendChild(tr);
    });
  }

  function renderDummyDataView(table, rows) {
    dummyTableHead.innerHTML = '';
    dummyTableBody.innerHTML = '';

    const cols = (table.fields || []).map(f => f.name);
    if (cols.length === 0 || rows.length === 0) {
      dummyTableBody.innerHTML = '<tr><td colspan="100" style="text-align:center; padding: 2rem;">No synthetic rows available.</td></tr>';
      return;
    }

    // Header
    const trHead = document.createElement('tr');
    cols.forEach(col => {
      const th = document.createElement('th');
      th.textContent = col;
      trHead.appendChild(th);
    });
    dummyTableHead.appendChild(trHead);

    // Rows
    rows.forEach(row => {
      const tr = document.createElement('tr');
      cols.forEach(col => {
        const td = document.createElement('td');
        const val = row[col];
        if (val === null || val === undefined) {
          td.innerHTML = '<span style="color: var(--text-muted);">NULL</span>';
        } else if (typeof val === 'boolean') {
          td.innerHTML = `<span class="badge ${val ? 'badge-measure' : 'badge-neutral'}">${val}</span>`;
        } else {
          td.textContent = String(val);
        }
        tr.appendChild(td);
      });
      dummyTableBody.appendChild(tr);
    });
  }

  function renderLlmSummaryView(table) {
    const summary = {
      name: table.name,
      label: table.label || table.name,
      source_connection: table.source_connection,
      remote_table: table.remote_table,
      key_columns: (table.fields || []).filter(f => f.is_key).map(f => f.name),
      fields: (table.fields || []).map(f => ({
        name: f.name,
        label: f.label,
        data_type: f.data_type,
        inferred_classification: f.inferred_classification,
        length: f.length,
        precision: f.precision,
        scale: f.scale,
        explicit_aggregation: f.explicit_aggregation,
      })),
      modeling_metadata: table.modeling_metadata,
      capabilities: table.capabilities,
    };
    llmJsonContent.textContent = JSON.stringify(summary, null, 2);
  }

  function renderLogs(logs, errors) {
    logList.innerHTML = '';
    logs.forEach(msg => {
      const li = document.createElement('li');
      li.textContent = msg;
      if (msg.toLowerCase().includes('error')) {
        li.classList.add('log-error');
      }
      logList.appendChild(li);
    });
    errors.forEach(err => {
      const li = document.createElement('li');
      li.className = 'log-error';
      li.textContent = `[ERROR] ${err}`;
      logList.appendChild(li);
    });
  }

  function switchView(viewName) {
    appState.activeView = viewName;
    viewTabs.forEach(t => {
      const isCurrent = t.getAttribute('data-view') === viewName;
      t.classList.toggle('active', isCurrent);
      t.setAttribute('aria-selected', isCurrent ? 'true' : 'false');
    });

    Object.entries(viewPanels).forEach(([key, panel]) => {
      if (key === viewName) {
        panel.classList.remove('hidden');
      } else {
        panel.classList.add('hidden');
      }
    });
  }

  function createChip(prefix, text, badgeClass) {
    const span = document.createElement('span');
    span.className = `badge ${badgeClass}`;
    span.innerHTML = `<strong>${escapeHtml(prefix)}</strong> ${escapeHtml(text)}`;
    return span;
  }

  function showError(msg) {
    errorMessage.textContent = msg;
    errorBanner.classList.remove('hidden');
  }

  function hideError() {
    errorBanner.classList.add('hidden');
  }

  function copyToClipboard(text, successMsg) {
    navigator.clipboard.writeText(text).then(() => {
      const prevTitle = document.title;
      document.title = `✓ ${successMsg}`;
      setTimeout(() => { document.title = prevTitle; }, 2000);
    });
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});
