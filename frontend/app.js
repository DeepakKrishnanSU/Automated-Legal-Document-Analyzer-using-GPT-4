/**
 * JurisAI - Enterprise Legal Document Analyzer
 * Frontend Application Controller (app.js)
 * Manages UI state, tab navigation, REST API communication,
 * and dynamic contract rendering.
 */

// ==============================================================================
// 1. APPLICATION STATE & CONFIGURATION
// ==============================================================================
const AppState = {
    activeTab: 'tab-dashboard',
    currentDoc: null,
    preprocessedData: null,
    promptData: null,
    analysisResult: null,
    backendStatus: {
        healthy: false,
        model: 'Connecting...',
        provider: 'ollama'
    }
};

const API_BASE = window.location.origin;

// ==============================================================================
// 2. DOM ELEMENT REFERENCES
// ==============================================================================
const DOM = {
    // Navigation & Layout
    sidebar: document.getElementById('appSidebar'),
    sidebarToggle: document.getElementById('btnToggleSidebar'),
    navItems: document.querySelectorAll('.nav-item'),
    workflowTabs: document.querySelectorAll('.workflow-tab'),
    breadcrumbCurrent: document.getElementById('currentBreadcrumb'),
    topContractName: document.getElementById('topContractName'),
    btnResetWorkflow: document.getElementById('btnResetWorkflow'),
    btnQuickAnalyze: document.getElementById('btnQuickAnalyze'),
    toastContainer: document.getElementById('toastContainer'),

    // Status elements
    statusDot: document.getElementById('statusDot'),
    statusModelName: document.getElementById('statusModelName'),
    statusSubtext: document.getElementById('statusSubtext'),
    badgeDocStatus: document.getElementById('badgeDocStatus'),
    badgeSections: document.getElementById('badgeSections'),
    pulseAnalysis: document.getElementById('pulseAnalysis'),

    // Dashboard
    btnStartIngest: document.getElementById('btnStartIngest'),
    btnLoadDemoNDA: document.getElementById('btnLoadDemoNDA'),
    metricDocName: document.getElementById('metricDocName'),
    metricDocType: document.getElementById('metricDocType'),
    metricWordCount: document.getElementById('metricWordCount'),
    metricCharCount: document.getElementById('metricCharCount'),
    metricSectionCount: document.getElementById('metricSectionCount'),
    metricChunkCount: document.getElementById('metricChunkCount'),
    metricInferenceTime: document.getElementById('metricInferenceTime'),
    metricEngineName: document.getElementById('metricEngineName'),
    pipelineCards: document.querySelectorAll('.pipeline-card'),

    // Ingest Tab
    sampleListContainer: document.getElementById('sampleContractsList'),
    inputDocTitle: document.getElementById('inputDocTitle'),
    inputDocText: document.getElementById('inputDocText'),
    liveCharCounter: document.getElementById('liveCharCounter'),
    btnClearTextInput: document.getElementById('btnClearTextInput'),
    btnSubmitTextInput: document.getElementById('btnSubmitTextInput'),

    // Extraction Preview Tab
    metaSource: document.getElementById('metaSource'),
    metaFormat: document.getElementById('metaFormat'),
    metaWords: document.getElementById('metaWords'),
    metaChars: document.getElementById('metaChars'),
    metaPages: document.getElementById('metaPages'),
    btnCopyRawText: document.getElementById('btnCopyRawText'),
    rawTextViewport: document.getElementById('rawTextViewport'),

    // Preprocess Tab
    btnRunPreprocess: document.getElementById('btnRunPreprocess'),
    statReduction: document.getElementById('statReduction'),
    statCleanChars: document.getElementById('statCleanChars'),
    statSectionCount: document.getElementById('statSectionCount'),
    statChunkCount: document.getElementById('statChunkCount'),
    tableSectionsBody: document.getElementById('tableSectionsBody'),
    cleanedTextViewport: document.getElementById('cleanedTextViewport'),

    // Prompt Tab
    systemPromptViewport: document.getElementById('systemPromptViewport'),
    userPromptViewport: document.getElementById('userPromptViewport'),

    // Summary Tab
    btnExecuteAnalysis: document.getElementById('btnExecuteAnalysis'),
    btnCopyFormattedReport: document.getElementById('btnCopyFormattedReport'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    loadingStatusText: document.getElementById('loadingStatusText'),
    resSummary: document.getElementById('resSummary'),
    resDocType: document.getElementById('resDocType'),
    resParties: document.getElementById('resParties'),
    resPurpose: document.getElementById('resPurpose'),
    resDuration: document.getElementById('resDuration'),
    resPayment: document.getElementById('resPayment'),
    resTermination: document.getElementById('resTermination'),
    resDates: document.getElementById('resDates'),
    resObligations: document.getElementById('resObligations'),
    resClauses: document.getElementById('resClauses'),
    rawLLMViewport: document.getElementById('rawLLMViewport'),

    // Export Tab
    btnSaveToDisk: document.getElementById('btnSaveToDisk'),
    saveDiskStatus: document.getElementById('saveDiskStatus'),
    btnDownloadBrowser: document.getElementById('btnDownloadBrowser'),
    reportPreviewViewport: document.getElementById('reportPreviewViewport')
};

// ==============================================================================
// 3. TOAST NOTIFICATION UTILITY
// ==============================================================================
function showToast(message, type = 'info', duration = 4000) {
    if (!DOM.toastContainer) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let iconClass = 'fa-circle-info';
    if (type === 'success') iconClass = 'fa-circle-check';
    if (type === 'error') iconClass = 'fa-triangle-exclamation';

    toast.innerHTML = `
        <i class="fa-solid ${iconClass}"></i>
        <span>${message}</span>
    `;

    DOM.toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ==============================================================================
// 4. TAB NAVIGATION CONTROLLER
// ==============================================================================
function switchTab(tabId) {
    DOM.navItems.forEach(item => {
        if (item.dataset.tab === tabId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    DOM.workflowTabs.forEach(tab => {
        if (tab.id === tabId) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    AppState.activeTab = tabId;

    // Update Breadcrumb label
    const activeNav = document.querySelector(`.nav-item[data-tab="${tabId}"] span`);
    if (activeNav && DOM.breadcrumbCurrent) {
        DOM.breadcrumbCurrent.textContent = activeNav.textContent;
    }

    // Scroll viewport to top on tab change
    const viewport = document.querySelector('.content-viewport');
    if (viewport) viewport.scrollTop = 0;
}

// ==============================================================================
// 5. REST API CLIENT FUNCTIONS
// ==============================================================================
async function fetchBackendStatus() {
    try {
        const res = await fetch(`${API_BASE}/api/status`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        AppState.backendStatus = data;

        if (DOM.statusModelName) {
            DOM.statusModelName.textContent = data.healthy
                ? `Ollama: ${data.model || 'Active'}`
                : 'Offline / Disconnected';
        }

        if (DOM.statusDot) {
            DOM.statusDot.style.background = data.healthy ? 'var(--brand-emerald)' : 'var(--brand-rose)';
            DOM.statusDot.style.boxShadow = data.healthy ? '0 0 6px var(--brand-emerald)' : '0 0 6px var(--brand-rose)';
        }

        if (DOM.metricEngineName) {
            DOM.metricEngineName.textContent = `Ollama: ${data.model || 'llama3.2'}`;
        }
    } catch (err) {
        console.warn('Backend status check failed:', err);
        if (DOM.statusModelName) DOM.statusModelName.textContent = 'Backend Offline';
        if (DOM.statusDot) DOM.statusDot.style.background = 'var(--brand-rose)';
    }
}

async function loadSampleContract(sampleFilename) {
    try {
        showToast(`Loading sample: ${sampleFilename}...`, 'info');
        const res = await fetch(`${API_BASE}/api/load-sample`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sample_name: sampleFilename })
        });

        const data = await res.json();
        if (!res.ok || !data.success) {
            throw new Error(data.error || 'Failed to load sample');
        }

        handleDocumentLoaded(data.document);
        showToast(`Successfully loaded '${data.document.source_name}'!`, 'success');
        switchTab('tab-extraction');
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    }
}

async function submitCustomText() {
    const text = DOM.inputDocText.value.trim();
    const title = DOM.inputDocTitle.value.trim() || 'Custom Legal Contract';

    if (!text) {
        showToast('Please enter or paste contract text first.', 'error');
        return;
    }

    try {
        showToast('Ingesting contract text...', 'info');
        const res = await fetch(`${API_BASE}/api/load-text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, title })
        });

        const data = await res.json();
        if (!res.ok || !data.success) {
            throw new Error(data.error || 'Failed to ingest text');
        }

        handleDocumentLoaded(data.document);
        showToast(`Contract '${title}' loaded successfully!`, 'success');
        switchTab('tab-extraction');
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    }
}

async function runPreprocessing() {
    if (!AppState.currentDoc) {
        showToast('Please load a document first.', 'error');
        switchTab('tab-ingest');
        return;
    }

    try {
        showToast('Preprocessing contract clauses & sections...', 'info');
        const res = await fetch(`${API_BASE}/api/preprocess`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await res.json();
        if (!res.ok || !data.success) {
            throw new Error(data.error || 'Preprocessing failed');
        }

        AppState.preprocessedData = data;
        AppState.promptData = data.prompt;

        renderPreprocessingResults(data);
        renderPromptStudio(data.prompt);
        showToast(`Parsed ${data.sections.length} clauses with Pandas!`, 'success');
    } catch (err) {
        showToast(`Preprocessing error: ${err.message}`, 'error');
    }
}

async function executeAIAnalysis() {
    if (!AppState.currentDoc) {
        showToast('Please load a document first.', 'error');
        switchTab('tab-ingest');
        return;
    }

    // Show loading state
    if (DOM.loadingOverlay) DOM.loadingOverlay.style.display = 'flex';
    if (DOM.pulseAnalysis) DOM.pulseAnalysis.style.display = 'block';

    try {
        const res = await fetch(`${API_BASE}/api/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await res.json();
        if (!res.ok || !data.success) {
            throw new Error(data.error || 'AI Analysis failed');
        }

        AppState.analysisResult = data.analysis;
        renderAnalysisResults(data.analysis);
        showToast(`Analysis completed in ${data.analysis.execution_time_sec}s!`, 'success');
    } catch (err) {
        showToast(`Analysis error: ${err.message}`, 'error');
    } finally {
        if (DOM.loadingOverlay) DOM.loadingOverlay.style.display = 'none';
        if (DOM.pulseAnalysis) DOM.pulseAnalysis.style.display = 'none';
    }
}

async function saveReportToDisk() {
    if (!AppState.analysisResult) {
        showToast('No analysis available to save. Please run inference first.', 'error');
        return;
    }

    try {
        showToast('Saving report to outputs/legal_analysis.txt...', 'info');
        const res = await fetch(`${API_BASE}/api/save-report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });

        const data = await res.json();
        if (!res.ok || !data.success) {
            throw new Error(data.error || 'Failed to save report');
        }

        if (DOM.saveDiskStatus) {
            DOM.saveDiskStatus.className = 'save-status-msg success';
            DOM.saveDiskStatus.textContent = `[✓] Successfully saved to: ${data.saved_path}`;
        }
        showToast('Report saved to outputs/ folder!', 'success');
    } catch (err) {
        if (DOM.saveDiskStatus) {
            DOM.saveDiskStatus.className = 'save-status-msg error';
            DOM.saveDiskStatus.textContent = `[!] Error: ${err.message}`;
        }
        showToast(`Save error: ${err.message}`, 'error');
    }
}

function downloadReportInBrowser() {
    if (!AppState.analysisResult || !AppState.analysisResult.formatted_report) {
        showToast('No analysis available to download.', 'error');
        return;
    }

    const reportContent = AppState.analysisResult.formatted_report;
    const blob = new Blob([reportContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');

    const cleanTitle = (AppState.currentDoc?.source_name || 'legal_analysis')
        .replace(/\.[^/.]+$/, "")
        .replace(/\s+/g, '_');

    link.href = url;
    link.download = `${cleanTitle}_analysis.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    showToast('Download started!', 'success');
}

// ==============================================================================
// 6. UI RENDERING LOGIC
// ==============================================================================
function handleDocumentLoaded(doc) {
    AppState.currentDoc = doc;
    AppState.preprocessedData = null;
    AppState.analysisResult = null;

    // Update Topbar Pill & Badge
    if (DOM.topContractName) DOM.topContractName.textContent = doc.source_name;
    if (DOM.badgeDocStatus) {
        DOM.badgeDocStatus.textContent = 'Loaded';
        DOM.badgeDocStatus.className = 'nav-badge ready-badge';
    }

    // Update Dashboard Metrics
    if (DOM.metricDocName) DOM.metricDocName.textContent = doc.source_name;
    if (DOM.metricDocType) DOM.metricDocType.textContent = `${doc.file_type.toUpperCase()} Contract`;
    if (DOM.metricWordCount) DOM.metricWordCount.textContent = doc.word_count.toLocaleString();
    if (DOM.metricCharCount) DOM.metricCharCount.textContent = `${doc.char_count.toLocaleString()} characters`;

    // Update Extraction Preview Viewport
    if (DOM.metaSource) DOM.metaSource.textContent = doc.source_name;
    if (DOM.metaFormat) DOM.metaFormat.textContent = doc.file_type.toUpperCase();
    if (DOM.metaWords) DOM.metaWords.textContent = doc.word_count.toLocaleString();
    if (DOM.metaChars) DOM.metaChars.textContent = doc.char_count.toLocaleString();
    if (DOM.metaPages) DOM.metaPages.textContent = doc.page_count;
    if (DOM.rawTextViewport) DOM.rawTextViewport.textContent = doc.raw_text;

    // Reset downstream fields
    resetDownstreamViews();
}

function renderPreprocessingResults(data) {
    const stats = data.stats;

    // Update Stats Bubbles
    if (DOM.statReduction) DOM.statReduction.textContent = `${stats.reduction_pct}%`;
    if (DOM.statCleanChars) DOM.statCleanChars.textContent = stats.cleaned_chars.toLocaleString();
    if (DOM.statSectionCount) DOM.statSectionCount.textContent = stats.section_count;
    if (DOM.statChunkCount) DOM.statChunkCount.textContent = data.chunk_count;

    // Update Dashboard Metrics
    if (DOM.metricSectionCount) DOM.metricSectionCount.textContent = stats.section_count;
    if (DOM.metricChunkCount) DOM.metricChunkCount.textContent = `${data.chunk_count} chunk(s)`;
    if (DOM.badgeSections) DOM.badgeSections.textContent = `${stats.section_count} Sections`;

    // Render Table of Sections
    if (DOM.tableSectionsBody) {
        DOM.tableSectionsBody.innerHTML = '';
        if (data.sections && data.sections.length > 0) {
            data.sections.forEach(sec => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-weight: 700; color: var(--brand-primary);">${sec.id}</td>
                    <td style="font-weight: 600; color: var(--text-primary);">${sec.title}</td>
                    <td style="font-family: var(--font-mono); color: var(--text-muted);">${sec.words}</td>
                    <td style="color: var(--text-secondary); font-size: 0.8rem;">${sec.snippet}</td>
                `;
                DOM.tableSectionsBody.appendChild(tr);
            });
        } else {
            DOM.tableSectionsBody.innerHTML = `<tr><td colspan="4" class="empty-table-msg">No distinct formal clauses identified.</td></tr>`;
        }
    }

    if (DOM.cleanedTextViewport) {
        DOM.cleanedTextViewport.textContent = data.cleaned_text;
    }
}

function renderPromptStudio(prompt) {
    if (!prompt) return;
    if (DOM.systemPromptViewport) DOM.systemPromptViewport.textContent = prompt.system_prompt;
    if (DOM.userPromptViewport) DOM.userPromptViewport.textContent = prompt.user_prompt;
}

function renderAnalysisResults(analysis) {
    const fields = analysis.parsed_fields || {};

    if (DOM.metricInferenceTime) {
        DOM.metricInferenceTime.textContent = `${analysis.execution_time_sec}s`;
    }

    // Populate Fields
    if (DOM.resSummary) DOM.resSummary.textContent = fields['Summary'] || analysis.raw_response;
    if (DOM.resDocType) DOM.resDocType.textContent = fields['Document Type'] || 'Not mentioned';
    if (DOM.resParties) DOM.resParties.textContent = fields['Parties'] || 'Not mentioned';
    if (DOM.resPurpose) DOM.resPurpose.textContent = fields['Purpose'] || 'Not mentioned';
    if (DOM.resDuration) DOM.resDuration.textContent = fields['Duration'] || 'Not mentioned';
    if (DOM.resPayment) DOM.resPayment.textContent = fields['Payment Terms'] || 'Not mentioned';
    if (DOM.resTermination) DOM.resTermination.textContent = fields['Termination Conditions'] || 'Not mentioned';
    if (DOM.resDates) DOM.resDates.textContent = fields['Important Dates'] || 'Not mentioned';
    if (DOM.resObligations) DOM.resObligations.textContent = fields['Key Obligations'] || 'Not mentioned';
    if (DOM.resClauses) DOM.resClauses.textContent = fields['Potentially Important Clauses'] || 'Not mentioned';

    if (DOM.rawLLMViewport) DOM.rawLLMViewport.textContent = analysis.raw_response;
    if (DOM.reportPreviewViewport) DOM.reportPreviewViewport.textContent = analysis.formatted_report;
}

function resetDownstreamViews() {
    if (DOM.statReduction) DOM.statReduction.textContent = '0.0%';
    if (DOM.statCleanChars) DOM.statCleanChars.textContent = '0';
    if (DOM.statSectionCount) DOM.statSectionCount.textContent = '0';
    if (DOM.statChunkCount) DOM.statChunkCount.textContent = '0';
    if (DOM.badgeSections) DOM.badgeSections.textContent = '0 Clauses';
    if (DOM.tableSectionsBody) {
        DOM.tableSectionsBody.innerHTML = `<tr><td colspan="4" class="empty-table-msg">Run ingestion and preprocessing to populate sections.</td></tr>`;
    }
    if (DOM.cleanedTextViewport) DOM.cleanedTextViewport.textContent = 'Cleaned text will appear here...';
    if (DOM.userPromptViewport) DOM.userPromptViewport.textContent = 'Load a contract to inspect prompt formulation...';

    // Clear Summary
    if (DOM.resSummary) DOM.resSummary.textContent = 'Load a contract and click "Run Inference" to generate analysis.';
    ['resDocType', 'resParties', 'resPurpose', 'resDuration', 'resPayment', 'resTermination', 'resDates', 'resObligations', 'resClauses']
        .forEach(id => { if (DOM[id]) DOM[id].textContent = 'Not analyzed'; });

    if (DOM.rawLLMViewport) DOM.rawLLMViewport.textContent = 'Raw response text will be displayed here...';
    if (DOM.reportPreviewViewport) DOM.reportPreviewViewport.textContent = 'No report generated yet. Run analysis first.';
    if (DOM.saveDiskStatus) DOM.saveDiskStatus.textContent = '';
}

function resetEntireWorkflow() {
    AppState.currentDoc = null;
    AppState.preprocessedData = null;
    AppState.promptData = null;
    AppState.analysisResult = null;

    if (DOM.topContractName) DOM.topContractName.textContent = 'No contract selected';
    if (DOM.badgeDocStatus) {
        DOM.badgeDocStatus.textContent = 'Empty';
        DOM.badgeDocStatus.className = 'nav-badge';
    }
    if (DOM.metricDocName) DOM.metricDocName.textContent = 'None';
    if (DOM.metricDocType) DOM.metricDocType.textContent = 'Waiting for document';
    if (DOM.metricWordCount) DOM.metricWordCount.textContent = '0';
    if (DOM.metricCharCount) DOM.metricCharCount.textContent = '0 characters';
    if (DOM.metricSectionCount) DOM.metricSectionCount.textContent = '0';
    if (DOM.metricChunkCount) DOM.metricChunkCount.textContent = '0 chunks';
    if (DOM.metricInferenceTime) DOM.metricInferenceTime.textContent = '--';

    if (DOM.inputDocTitle) DOM.inputDocTitle.value = '';
    if (DOM.inputDocText) DOM.inputDocText.value = '';
    if (DOM.liveCharCounter) DOM.liveCharCounter.textContent = '0 words • 0 characters';
    if (DOM.rawTextViewport) DOM.rawTextViewport.textContent = 'No document loaded yet.';

    resetDownstreamViews();
    switchTab('tab-dashboard');
    showToast('Application state reset to blank.', 'info');
}

// ==============================================================================
// 7. EVENT LISTENERS ATTACHMENT
// ==============================================================================
function initEventListeners() {
    // Tab switching via sidebar
    DOM.navItems.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.dataset.tab;
            if (targetTab) switchTab(targetTab);
        });
    });

    // Pipeline cards click navigation
    DOM.pipelineCards.forEach(card => {
        card.addEventListener('click', () => {
            const target = card.dataset.target;
            if (target) switchTab(target);
        });
    });

    // Mobile sidebar toggle
    if (DOM.sidebarToggle && DOM.sidebar) {
        DOM.sidebarToggle.addEventListener('click', () => {
            DOM.sidebar.classList.toggle('open');
        });
    }

    // Dashboard CTA Buttons
    if (DOM.btnStartIngest) {
        DOM.btnStartIngest.addEventListener('click', () => switchTab('tab-ingest'));
    }
    if (DOM.btnLoadDemoNDA) {
        DOM.btnLoadDemoNDA.addEventListener('click', () => loadSampleContract('sample_nda.txt'));
    }

    // Reset workflow
    if (DOM.btnResetWorkflow) {
        DOM.btnResetWorkflow.addEventListener('click', resetEntireWorkflow);
    }

    // Run Full Pipeline
    if (DOM.btnQuickAnalyze) {
        DOM.btnQuickAnalyze.addEventListener('click', async () => {
            if (!AppState.currentDoc) {
                showToast('Auto-loading sample NDA to demonstrate full pipeline...', 'info');
                await loadSampleContract('sample_nda.txt');
            }
            await runPreprocessing();
            switchTab('tab-summary');
            await executeAIAnalysis();
        });
    }

    // Sample Contracts Buttons
    document.querySelectorAll('.sample-item').forEach(item => {
        const btn = item.querySelector('.btn-load-sample');
        const filename = item.dataset.filename;
        if (btn && filename) {
            btn.addEventListener('click', () => loadSampleContract(filename));
        }
    });

    // Custom text input counter & actions
    if (DOM.inputDocText) {
        DOM.inputDocText.addEventListener('input', () => {
            const text = DOM.inputDocText.value;
            const chars = text.length;
            const words = text.trim() ? text.trim().split(/\s+/).length : 0;
            if (DOM.liveCharCounter) {
                DOM.liveCharCounter.textContent = `${words.toLocaleString()} words • ${chars.toLocaleString()} characters`;
            }
        });
    }

    if (DOM.btnClearTextInput) {
        DOM.btnClearTextInput.addEventListener('click', () => {
            if (DOM.inputDocText) DOM.inputDocText.value = '';
            if (DOM.inputDocTitle) DOM.inputDocTitle.value = '';
            if (DOM.liveCharCounter) DOM.liveCharCounter.textContent = '0 words • 0 characters';
        });
    }

    if (DOM.btnSubmitTextInput) {
        DOM.btnSubmitTextInput.addEventListener('click', submitCustomText);
    }

    // Copy raw text button
    if (DOM.btnCopyRawText) {
        DOM.btnCopyRawText.addEventListener('click', () => {
            if (AppState.currentDoc && AppState.currentDoc.raw_text) {
                navigator.clipboard.writeText(AppState.currentDoc.raw_text);
                showToast('Raw contract text copied to clipboard!', 'success');
            } else {
                showToast('No contract text available to copy.', 'error');
            }
        });
    }

    // Preprocessing button
    if (DOM.btnRunPreprocess) {
        DOM.btnRunPreprocess.addEventListener('click', runPreprocessing);
    }

    // AI Analysis execution button
    if (DOM.btnExecuteAnalysis) {
        DOM.btnExecuteAnalysis.addEventListener('click', executeAIAnalysis);
    }

    // Copy formatted report button
    if (DOM.btnCopyFormattedReport) {
        DOM.btnCopyFormattedReport.addEventListener('click', () => {
            if (AppState.analysisResult && AppState.analysisResult.formatted_report) {
                navigator.clipboard.writeText(AppState.analysisResult.formatted_report);
                showToast('Formatted legal report copied to clipboard!', 'success');
            } else {
                showToast('No analysis report available to copy.', 'error');
            }
        });
    }

    // Save to Disk & Download in Browser
    if (DOM.btnSaveToDisk) {
        DOM.btnSaveToDisk.addEventListener('click', saveReportToDisk);
    }
    if (DOM.btnDownloadBrowser) {
        DOM.btnDownloadBrowser.addEventListener('click', downloadReportInBrowser);
    }
}

// ==============================================================================
// 8. APP INITIALIZATION
// ==============================================================================
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    fetchBackendStatus();
    console.log('JurisAI Application Controller initialized successfully.');
});
