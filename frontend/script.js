// Global variables
let selectedFile = null;
let analysisInProgress = false;
let socket = null;
let currentSessionId = null;

// DOM elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const removeFile = document.getElementById('removeFile');
const targetRole = document.getElementById('targetRole');
const analyzeBtn = document.getElementById('analyzeBtn');
const resetBtn = document.getElementById('resetBtn');
const progressSection = document.getElementById('progressSection');
const resultsSection = document.getElementById('resultsSection');
const loadingOverlay = document.getElementById('loadingOverlay');

// Configuration elements
const modelSelect = document.getElementById('modelSelect');
const apiSourceSelect = document.getElementById('apiSourceSelect');
const extractionSelect = document.getElementById('extractionSelect');
const analysisModeRadios = document.querySelectorAll('input[name="analysisMode"]');

// Header configuration display
const activeModel = document.getElementById('activeModel');
const activeApiSource = document.getElementById('activeApiSource');
const activeExtraction = document.getElementById('activeExtraction');

// Agent cards
const cvParserCard = document.getElementById('cvParserCard');
const skillAnalystCard = document.getElementById('skillAnalystCard');
const marketIntelCard = document.getElementById('marketIntelCard');
const reportGenCard = document.getElementById('reportGenCard');

// Progress elements
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');

// Agent details elements
const cvParserDetails = document.getElementById('cvParserDetails');
const skillAnalystDetails = document.getElementById('skillAnalystDetails');
const marketIntelDetails = document.getElementById('marketIntelDetails');
const reportGenDetails = document.getElementById('reportGenDetails');

// Agent technology elements
const cvParserTech = document.getElementById('cvParserTech');
const skillAnalystTech = document.getElementById('skillAnalystTech');
const marketIntelTech = document.getElementById('marketIntelTech');
const reportGenTech = document.getElementById('reportGenTech');

// Results elements
const candidateName = document.getElementById('candidateName');
const technicalSkills = document.getElementById('technicalSkills');
const implicitSkills = document.getElementById('implicitSkills');
const experience = document.getElementById('experience');
const marketDemand = document.getElementById('marketDemand');
const salaryRange = document.getElementById('salaryRange');
const reportContent = document.getElementById('reportContent');

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    initializeWebSocket();
});

function initializeEventListeners() {
    // File upload events
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);
    removeFile.addEventListener('click', clearFile);

    // Analysis events
    targetRole.addEventListener('input', validateForm);
    analyzeBtn.addEventListener('click', startAnalysis);
    resetBtn.addEventListener('click', resetAnalysis);

    // Configuration events
    modelSelect.addEventListener('change', updateHeaderConfig);
    apiSourceSelect.addEventListener('change', updateHeaderConfig);
    extractionSelect.addEventListener('change', updateHeaderConfig);
    analysisModeRadios.forEach(radio => {
        radio.addEventListener('change', updateHeaderConfig);
    });

    // Action buttons
    document.getElementById('downloadReport').addEventListener('click', downloadReport);
    document.getElementById('newAnalysis').addEventListener('click', resetAnalysis);
    document.getElementById('downloadMd').addEventListener('click', () => downloadReport('md'));
    document.getElementById('downloadTxt').addEventListener('click', () => downloadReport('txt'));
    document.getElementById('viewFullReport').addEventListener('click', viewFullReport);

    // Initialize header configuration
    updateHeaderConfig();
    
    // Check API availability and update configuration
    checkApiAvailability();
}

// WebSocket functionality
function initializeWebSocket() {
    try {
        // Initialize Socket.IO client
        socket = io();
        
        socket.on('connect', function() {
            console.log('Connected to analysis server');
        });
        
        socket.on('disconnect', function() {
            console.log('Disconnected from analysis server');
        });
        
        socket.on('connected', function(data) {
            console.log('Server message:', data.message);
        });
        
        socket.on('joined', function(data) {
            console.log('Joined session:', data.session_id);
        });
        
        socket.on('analysis_update', function(data) {
            handleAnalysisUpdate(data);
        });
        
    } catch (error) {
        console.error('WebSocket initialization failed:', error);
        // Fallback to polling if WebSocket fails
        console.log('Falling back to polling mode');
    }
}

function handleAnalysisUpdate(data) {
    console.log('Analysis update:', data);
    
    switch (data.type) {
        case 'progress':
            updateProgress(data.percent, data.message);
            break;
            
        case 'agent_status':
            updateAgentStatus(data.agent, data.status_class, data.status, '');
            break;
            
        case 'log':
            addLogEntry(data.level, data.message);
            break;
            
        case 'result':
            updateResults(data.result);
            showResults();
            break;
            
        case 'error':
            showError(data.message);
            break;
            
        case 'show_agents':
            showProgressSection();
            break;
            
        default:
            console.log('Unknown update type:', data.type);
    }
}

function updateProgress(percent, message) {
    if (progressFill) {
        progressFill.style.width = percent + '%';
    }
    if (progressText) {
        progressText.textContent = message;
    }
}

function addLogEntry(level, message) {
    // Add log entry to a log section if it exists
    const logContainer = document.getElementById('logContainer');
    const logSection = document.getElementById('logSection');
    
    if (logContainer && logSection) {
        // Show log section if it's hidden
        if (logSection.style.display === 'none') {
            logSection.style.display = 'block';
        }
        
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${level.toLowerCase()}`;
        logEntry.innerHTML = `<span class="log-time">${new Date().toLocaleTimeString()}</span> <span class="log-level">[${level}]</span> ${message}`;
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
    }
}

// File handling functions
function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

function handleFile(file) {
    // Validate file type
    const allowedTypes = ['application/pdf', 'application/msword', 
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                         'text/plain'];
    
    if (!allowedTypes.includes(file.type)) {
        alert('Please select a valid file type (PDF, DOC, DOCX, or TXT)');
        return;
    }

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
        alert('File size must be less than 10MB');
        return;
    }

    selectedFile = file;
    displayFileInfo(file);
    validateForm();
}

function displayFileInfo(file) {
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    uploadArea.style.display = 'none';
    fileInfo.style.display = 'flex';
}

function clearFile() {
    selectedFile = null;
    fileInput.value = '';
    uploadArea.style.display = 'block';
    fileInfo.style.display = 'none';
    validateForm();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function validateForm() {
    const isValid = selectedFile && targetRole.value.trim().length > 0;
    analyzeBtn.disabled = !isValid;
}

// Analysis functions
async function startAnalysis() {
    if (analysisInProgress) return;
    
    analysisInProgress = true;
    showLoadingOverlay();
    resetProgress();
    showProgressSection();
    
    try {
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('role', targetRole.value.trim());
        
        // Add configuration data
        formData.append('model', modelSelect.value);
        formData.append('api_source', apiSourceSelect.value);
        formData.append('extraction_method', extractionSelect.value);
        formData.append('analysis_mode', document.querySelector('input[name="analysisMode"]:checked').value);
        
        // Set RAG based on API source selection
        formData.append('use_rag', apiSourceSelect.value === 'rag' ? 'true' : 'false');
        formData.append('verbose', 'true');
        
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        currentSessionId = result.session_id;
        
        // Join the analysis session for real-time updates
        if (socket && currentSessionId) {
            socket.emit('join_analysis', { session_id: currentSessionId });
        }
        
        // Hide loading overlay since we'll get real-time updates
        hideLoadingOverlay();
        
    } catch (error) {
        console.error('Analysis failed:', error);
        showError('Analysis failed. Please try again.');
        analysisInProgress = false;
        hideLoadingOverlay();
    }
}

function updateResults(results) {
    candidateName.textContent = results.candidate_name || '-';
    technicalSkills.textContent = Array.isArray(results.technical_skills) ? results.technical_skills.length : '-';
    implicitSkills.textContent = Array.isArray(results.implicit_skills) ? results.implicit_skills.length : '-';
    experience.textContent = results.years_experience || '-';
    marketDemand.textContent = results.market_demand || '-';
    salaryRange.textContent = results.salary_range || '-';
    
    if (results.report_path) {
        // Load report content from the generated report file
        loadReportContent(results.report_path);
    }
    
    // Update analysis status
    analysisInProgress = false;
}

function loadReportContent(reportPath) {
    // Extract session ID from report path for the API call
    const sessionId = currentSessionId;
    if (sessionId) {
        fetch(`/api/report/${sessionId}`)
            .then(response => {
                if (response.ok) {
                    return response.text();
                }
                throw new Error('Failed to load report');
            })
            .then(reportText => {
                // Clear placeholder and show formatted report
                reportContent.innerHTML = formatReportContent(reportText);
                
                // Add expandable functionality
                initializeExpandableSections();
            })
            .catch(error => {
                console.error('Error loading report:', error);
                reportContent.innerHTML = `
                    <div class="report-error">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>Failed to load report content. Please try downloading the report instead.</p>
                    </div>
                `;
            });
    }
}

function formatReportContent(content) {
    // Convert markdown content to enhanced HTML
    let formatted = content;
    
    // Convert headers
    formatted = formatted.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    formatted = formatted.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    formatted = formatted.replace(/^# (.*$)/gim, '<h1>$1</h1>');
    
    // Convert bold and italic
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Convert lists
    formatted = formatted.replace(/^- (.*$)/gim, '<li>$1</li>');
    formatted = formatted.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
    
    // Convert tables
    const tableRegex = /\|(.+)\|\n\|[-\s|]+\|\n((?:\|.+\|\n?)*)/g;
    formatted = formatted.replace(tableRegex, (match, header, rows) => {
        const headers = header.split('|').map(h => h.trim()).filter(h => h);
        const headerRow = headers.map(h => `<th>${h}</th>`).join('');
        
        const rowLines = rows.trim().split('\n');
        const bodyRows = rowLines.map(row => {
            const cells = row.split('|').map(c => c.trim()).filter(c => c);
            return `<tr>${cells.map(c => `<td>${c}</td>`).join('')}</tr>`;
        }).join('');
        
        return `<table class="result-table"><thead><tr>${headerRow}</tr></thead><tbody>${bodyRows}</tbody></table>`;
    });
    
    // Convert paragraphs
    formatted = formatted.replace(/\n\n/g, '</p><p>');
    formatted = formatted.replace(/\n/g, '<br>');
    
    // Wrap in paragraph tags
    formatted = `<p>${formatted}</p>`;
    
    return `<div class="formatted-report">${formatted}</div>`;
}

function initializeExpandableSections() {
    // Add expandable functionality to sections
    const sections = reportContent.querySelectorAll('h2, h3');
    sections.forEach(section => {
        const nextElement = section.nextElementSibling;
        if (nextElement && (nextElement.tagName === 'P' || nextElement.tagName === 'UL' || nextElement.tagName === 'TABLE')) {
            // Create expandable section
            const expandableSection = document.createElement('div');
            expandableSection.className = 'expandable-section';
            
            const header = document.createElement('div');
            header.className = 'expandable-header';
            header.innerHTML = `
                <span>${section.textContent}</span>
                <i class="fas fa-chevron-down expand-icon"></i>
            `;
            
            const content = document.createElement('div');
            content.className = 'expandable-content';
            
            // Move content after the header into the expandable content
            let currentElement = section.nextElementSibling;
            while (currentElement && !['H1', 'H2', 'H3', 'H4'].includes(currentElement.tagName)) {
                const nextSibling = currentElement.nextElementSibling;
                content.appendChild(currentElement);
                currentElement = nextSibling;
            }
            
            expandableSection.appendChild(header);
            expandableSection.appendChild(content);
            
            // Replace the original section with expandable version
            section.parentNode.insertBefore(expandableSection, section);
            section.remove();
            
            // Add click handler
            header.addEventListener('click', () => {
                const isExpanded = content.classList.contains('expanded');
                const icon = header.querySelector('.expand-icon');
                
                if (isExpanded) {
                    content.classList.remove('expanded');
                    icon.classList.remove('expanded');
                } else {
                    content.classList.add('expanded');
                    icon.classList.add('expanded');
                }
            });
        }
    });
}

function formatReport(report) {
    // Convert markdown-like content to HTML
    let html = report
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
    
    return `<p>${html}</p>`;
}

function showLoadingOverlay() {
    loadingOverlay.style.display = 'flex';
}

function hideLoadingOverlay() {
    loadingOverlay.style.display = 'none';
}

function showProgressSection() {
    progressSection.style.display = 'block';
    resultsSection.style.display = 'none';
}

function showResults() {
    resultsSection.style.display = 'block';
    progressSection.style.display = 'none';
}

function resetProgress() {
    progressFill.style.width = '0%';
    progressText.textContent = 'Initializing...';
    
    // Reset all agent cards with technology information
    const agentConfigs = [
        { agent: 'cvParser', tech: getExtractionTechnology() },
        { agent: 'skillAnalyst', tech: getModelTechnology() },
        { agent: 'marketIntel', tech: getApiSourceTechnology() },
        { agent: 'reportGen', tech: getModelTechnology() }
    ];
    
    agentConfigs.forEach(config => {
        updateAgentStatus(config.agent, 'waiting', 'Waiting...', '', config.tech);
    });
}

function getExtractionTechnology() {
    const method = extractionSelect.value;
    switch(method) {
        case 'regex_ner': return 'Regex + NER';
        case 'spacy': return 'spaCy NER';
        case 'regex': return 'Regex Patterns';
        case 'llm': return 'LLM Extraction';
        default: return 'Regex + NER';
    }
}

function getModelTechnology() {
    const model = modelSelect.value;
    switch(model) {
        case 'ollama': return 'Local LLM';
        case 'anthropic': return 'Claude API';
        case 'openai': return 'GPT API';
        case 'template': return 'Template-based';
        default: return 'Local LLM';
    }
}

function getApiSourceTechnology() {
    const source = apiSourceSelect.value;
    switch(source) {
        case 'static': return 'Static Data';
        case 'rag': return 'JSearch API';
        case 'linkedin': return 'LinkedIn API';
        default: return 'Static Data';
    }
}

function resetAnalysis() {
    selectedFile = null;
    targetRole.value = '';
    fileInput.value = '';
    uploadArea.style.display = 'block';
    fileInfo.style.display = 'none';
    progressSection.style.display = 'none';
    resultsSection.style.display = 'none';
    validateForm();
}

function showError(message) {
    console.error('Analysis error:', message);
    
    // Create a more user-friendly error display
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `
        <div class="error-content">
            <i class="fas fa-exclamation-triangle"></i>
            <h3>Analysis Error</h3>
            <p>${message}</p>
            <button onclick="this.parentElement.parentElement.remove()" class="btn btn-secondary">Close</button>
        </div>
    `;
    
    // Add error styles if not already present
    if (!document.getElementById('error-styles')) {
        const style = document.createElement('style');
        style.id = 'error-styles';
        style.textContent = `
            .error-message {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                z-index: 1001;
                max-width: 400px;
                text-align: center;
            }
            .error-content i {
                color: #e74c3c;
                font-size: 2rem;
                margin-bottom: 10px;
            }
            .error-content h3 {
                color: #e74c3c;
                margin-bottom: 10px;
            }
            .error-content p {
                color: #555;
                margin-bottom: 15px;
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(errorDiv);
    
    // Reset analysis state
    analysisInProgress = false;
    hideLoadingOverlay();
}

function downloadReport(format = 'txt') {
    if (!currentSessionId) {
        alert('No report available to download');
        return;
    }
    
    // Get report content from the server
    fetch(`/api/report/${currentSessionId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Report not found');
            }
            return response.text();
        })
        .then(reportText => {
            // Create blob with appropriate MIME type
            const mimeType = format === 'md' ? 'text/markdown' : 'text/plain';
            const blob = new Blob([reportText], { type: mimeType });
            const url = URL.createObjectURL(blob);
            
            // Create download link
            const a = document.createElement('a');
            a.href = url;
            a.download = `cv-analysis-report-${new Date().toISOString().split('T')[0]}.${format}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error('Download failed:', error);
            alert('Failed to download report. Please try again.');
        });
}

function updateHeaderConfig() {
    // Update header display with current configuration
    const modelText = modelSelect.options[modelSelect.selectedIndex].text;
    const apiText = apiSourceSelect.options[apiSourceSelect.selectedIndex].text;
    const extractionText = extractionSelect.options[extractionSelect.selectedIndex].text;
    
    activeModel.textContent = modelText;
    activeApiSource.textContent = apiText;
    activeExtraction.textContent = extractionText;
}

async function checkApiAvailability() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();
        
        // Update model options based on availability
        updateModelOptions(status);
        updateApiSourceOptions(status);
        
    } catch (error) {
        console.log('API status check failed, using default configuration');
        // Keep default options if API check fails
    }
}

function updateModelOptions(status) {
    // Disable options that are not available
    const modelOptions = modelSelect.querySelectorAll('option');
    modelOptions.forEach(option => {
        if (option.value === 'anthropic' && !status.features?.anthropic_available) {
            option.disabled = true;
            option.textContent += ' (Not Available)';
        } else if (option.value === 'openai' && !status.features?.openai_available) {
            option.disabled = true;
            option.textContent += ' (Not Available)';
        }
    });
}

function updateApiSourceOptions(status) {
    // Disable options that are not available
    const apiOptions = apiSourceSelect.querySelectorAll('option');
    apiOptions.forEach(option => {
        if (option.value === 'rag' && !status.features?.rag_enabled) {
            option.disabled = true;
            option.textContent += ' (Not Available)';
        } else if (option.value === 'linkedin' && !status.features?.linkedin_available) {
            option.disabled = true;
            option.textContent += ' (Not Available)';
        }
    });
}

function updateAgentStatus(agent, status, message, details = '', technology = '') {
    const card = document.getElementById(agent + 'Card');
    const statusElement = card.querySelector('.agent-status');
    const detailsElement = document.getElementById(agent + 'Details');
    const techElement = document.getElementById(agent + 'Tech');
    const statusIcon = card.querySelector('.agent-status-icon');
    
    // Update card class
    card.className = `agent-card ${status}`;
    
    // Update status text
    statusElement.textContent = message;
    
    // Update details
    if (details) {
        detailsElement.innerHTML = details;
    }
    
    // Update technology display
    if (technology && techElement) {
        techElement.textContent = technology;
    }
    
    // Update status icon
    const iconClass = status === 'active' ? 'fas fa-spinner fa-spin' :
                     status === 'completed' ? 'fas fa-check' :
                     status === 'error' ? 'fas fa-times' : 'fas fa-clock';
    statusIcon.className = `agent-status-icon ${iconClass}`;
}

function viewFullReport() {
    if (!currentSessionId) {
        showError('No analysis session found. Please run an analysis first.');
        return;
    }
    
    // Open the report in a new tab/window
    const reportUrl = `/report/${currentSessionId}`;
    window.open(reportUrl, '_blank');
}