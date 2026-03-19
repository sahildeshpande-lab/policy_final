/* ── NEXUS HR — Production App Script ─────────────────── */

let currentThreadId = null;
let requestType = "Any Query";
let flowFormData = {};
let flowStep = -1;

/* ── FLOWS ─────────────────────────────────────────────── */
const FLOWS = {
    "Leave Apply": {
        endpoint: `/leave_apply`,
        successMsg: "Your leave application has been submitted successfully! 🎉",
        questions: [
            { key: "name", q: "Sure! May I know your full name?" },
            { key: "empId", q: "Great — could you please share your Employee ID? (e.g. SOL123)" },
            {
                key: "leaveGrade",
                q: "What type of leave would you like to apply for?",
                options: [
                    { value: "1", label: "Planned Leave (PLY)" },
                    { value: "2", label: "Leave Intimation (Already Taken)" }
                ]
            },
            { key: "leaveStartDate", q: "When will your leave start?", inputType: "date" },
            { key: "leaveEndDate", q: "And when will your leave end?", inputType: "date" },
            {
                key: "leaveType",
                q: "Got it! Please select your leave type:",
                options: [
                    { value: "0", label: "Full Day" },
                    { value: "1", label: "First Half" },
                    { value: "2", label: "Second Half" },
                    { value: "3", label: "Multiple Days" },
                    { value: "4", label: "Early Leave" },
                    { value: "5", label: "Short Break" }
                ]
            },
            {
                key: "leaveCategory",
                q: "Which leave category should I mark for you?",
                options: [
                    { value: "1", label: "Sick Leave" },
                    { value: "2", label: "Casual Leave" },
                    { value: "3", label: "Complementary Leave" }
                ]
            },
            { key: "leaveContent", q: "Please share the reason for your leave." },
            { key: "managerId", q: "Lastly, may I know your Manager's ID?" }
        ],
        formatData: async (fd) => {
            const rawSalt = `${Date.now()}_${fd.name}_${fd.empId}_${fd.managerId}`;
            const encoder = new TextEncoder();
            const data = encoder.encode(rawSalt);
            const hashBuffer = await crypto.subtle.digest('SHA-256', data);
            const hashArray = Array.from(new Uint8Array(hashBuffer));
            const salt = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
            return {
                name: fd.name, empId: fd.empId,
                leaveGrade: parseInt(fd.leaveGrade) || 1,
                leaveStartDate: fd.leaveStartDate, leaveEndDate: fd.leaveEndDate,
                leaveType: parseInt(fd.leaveType) || 0,
                leaveCategory: parseInt(fd.leaveCategory) || 1,
                leaveContent: fd.leaveContent, managerId: fd.managerId,
                salt, thread_id: currentThreadId
            };
        },
        formatSummary: (fd) => (
            `Here's a summary of your leave request:\n\n` +
            `• Name: ${fd.name}\n• Employee ID: ${fd.empId}\n• Manager ID: ${fd.managerId}\n` +
            `• Leave Grade: ${fd.leaveGrade}\n• Leave Type: ${fd.leaveType}\n• Category: ${fd.leaveCategory}\n` +
            `• Dates: ${fd.leaveStartDate} → ${fd.leaveEndDate}\n• Reason: ${fd.leaveContent}`
        )
    },
    "Apply WFH": {
        endpoint: `/wfh_apply`,
        successMsg: "Your WFH request has been submitted successfully! 🏠✨",
        questions: [
            { key: "empId", q: "Please share your Employee ID." },
            {
                key: "is_extra_request",
                q: "Is this a regular WFH request or an extra WFH request beyond your monthly quota?",
                options: [
                    { value: "0", label: "Normal (Within Quota)" },
                    { value: "1", label: "Extra (Exceeded Quota)" }
                ]
            },
            { key: "wfhStartDate", q: "When would you like your WFH to start?", inputType: "date" },
            { key: "wfhEndDate", q: "And when will it end?", inputType: "date" },
            { key: "reason", q: "Please share the reason for your WFH request. (Type 'NA' if none)" },
            { key: "managerId", q: "What is your Manager's ID?" }
        ],
        formatData: (fd) => ({
            empId: fd.empId, wfhStartDate: fd.wfhStartDate, wfhEndDate: fd.wfhEndDate,
            reason: fd.reason, is_extra_request: parseInt(fd.is_extra_request) || 0,
            managerId: fd.managerId, thread_id: currentThreadId
        }),
        formatSummary: (fd) => {
            const reqTypeStr = fd.is_extra_request === "1"
                ? "Extra WFH Request (Escalated to HR)"
                : "Normal WFH Request (Sent to Manager)";
            return `Summary of your WFH request:\n\n` +
                `• Employee ID: ${fd.empId}\n• Manager ID: ${fd.managerId}\n• Request Type: ${reqTypeStr}\n` +
                `• Dates: ${fd.wfhStartDate} → ${fd.wfhEndDate}\n• Reason: ${fd.reason}`;
        }
    },
    "IT Ticket Raised": {
        endpoint: `/it_ticket_apply`,
        successMsg: "Your IT/Helpdesk ticket has been submitted successfully! 🛠️",
        questions: [
            { key: "EmployeeId", q: "Let's get started! Please enter your Employee ID (e.g., SOL123)." },
            { key: "managerId", q: "Thanks! What is your Manager's ID?" },
            {
                key: "category_id",
                q: "Please select the category that best matches your issue:",
                options: [
                    { value: "4", label: "Machine Performance Issues" },
                    { value: "5", label: "Information Security Concern" },
                    { value: "7", label: "Hardware Support Needed" },
                    { value: "8", label: "Application/Software Support" },
                    { value: "10", label: "General IT Issue" },
                    { value: "11", label: "HR – Documents Needed" },
                    { value: "12", label: "HR – Other Queries" },
                    { value: "9", label: "Request for IT Peripherals" },
                    { value: "0", label: "Other / Not Listed" }
                ]
            },
            { key: "title", q: "Please provide a short title for your issue." },
            { key: "description", q: "Could you describe the issue in more detail?" },
            { key: "attachment", q: "If you have any screenshot or document, please upload it here. (Optional)", inputType: "file" }
        ],
        formatData: (fd) => ({
            EmployeeId: fd.EmployeeId, category_id: parseInt(fd.category_id) || 0,
            title: fd.title, description: fd.description,
            attachment: fd.attachment === 'NA' ? '' : fd.attachment,
            managerId: fd.managerId, thread_id: currentThreadId
        }),
        formatSummary: (fd) => {
            const itCats = [4, 5, 6, 7, 8, 10];
            const hrCats = [11, 12];
            let emailRoute = `${fd.managerId}@company.com`;
            let deptRoute = "Your Manager";
            if (itCats.includes(parseInt(fd.category_id))) { emailRoute = "teamit@solacetechnologies.co.in"; deptRoute = "IT Department"; }
            else if (hrCats.includes(parseInt(fd.category_id))) { emailRoute = "hr.mgr@solacetechnologies.co.in"; deptRoute = "HR Department"; }
            return `Summary of your IT ticket:\n\n` +
                `• Employee ID: ${fd.EmployeeId}\n• Manager ID: ${fd.managerId}\n• Category: ${fd.category_id}\n` +
                `• Title: ${fd.title}\n• Description: ${fd.description}\n• Attachment: ${fd.attachment || "None"}\n` +
                `• Routed To: ${deptRoute} (${emailRoute})`;
        }
    }
};

/* ── INIT ───────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
    loadConversations();
    setupEventListeners();
    setupErrorHandling();
    setupShowcase();
    setupDragDrop();
});

/* ── LOADING ────────────────────────────────────────────── */
function showLoading(message = "Processing…") {
    const overlay = document.getElementById('loadingOverlay');
    const text = document.getElementById('loadingText');
    if (text) text.textContent = message;
    overlay.classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden');
}

/* ── TOASTS ────────────────────────────────────────────── */
function showError(message) {
    const toast = document.getElementById('errorToast');
    toast.querySelector('.error-message').textContent = message;
    toast.classList.remove('hidden');
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => toast.classList.add('hidden'), 5000);
}

function showSuccess(message) {
    const toast = document.getElementById('successToast');
    toast.querySelector('.success-message').textContent = message;
    toast.classList.remove('hidden');
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => toast.classList.add('hidden'), 4000);
}

/* ── ERROR HANDLING ─────────────────────────────────────── */
function setupErrorHandling() {
    document.querySelector('.error-close')?.addEventListener('click', () => {
        document.getElementById('errorToast').classList.add('hidden');
    });
    window.addEventListener('unhandledrejection', (e) => {
        showError('An unexpected error occurred. Please try again.');
        console.error('Unhandled rejection:', e.reason);
    });
    window.addEventListener('error', (e) => {
        showError('An unexpected error occurred. Please try again.');
        console.error('Global error:', e.error);
    });
}

/* ── VALIDATION ─────────────────────────────────────────── */
function validateInput(value, type = 'text') {
    if (!value || value.trim() === '') return { valid: false, message: 'This field is required.' };
    if (type === 'email') {
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value))
            return { valid: false, message: 'Please enter a valid email address.' };
    }
    if (type === 'employeeId') {
        if (!/^SOL\d+/i.test(value))
            return { valid: false, message: 'Employee ID should start with SOL followed by numbers (e.g., SOL123).' };
    }
    if (type === 'date') {
        const sel = new Date(value);
        const today = new Date(); today.setHours(0,0,0,0);
        if (sel < today) return { valid: false, message: 'Date cannot be in the past.' };
    }
    return { valid: true };
}

/* ── EVENT LISTENERS ────────────────────────────────────── */
function setupEventListeners() {
    document.getElementById('uploadBtn').addEventListener('click', uploadPdf);
    document.getElementById('pdfUpload').addEventListener('change', () => {
        const f = document.getElementById('pdfUpload').files[0];
        if (f) document.getElementById('uploadStatus').textContent = `Selected: ${f.name}`;
    });

    document.getElementById('newChatBtn').addEventListener('click', resetChat);

    document.getElementById('sendBtn').addEventListener('click', sendMessage);
    document.getElementById('chatInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });

    document.querySelectorAll('.cat-pill').forEach(btn => {
        btn.addEventListener('click', (e) => {
            activateCategory(e.currentTarget.dataset.type);
        });
    });

    document.getElementById('logoutBtn')?.addEventListener('click', () => {
        if (confirm('Are you sure you want to logout?')) window.location.href = '/logout';
    });

    // Bar pills (header) — kept in sync with welcome-screen cat-pills
    document.querySelectorAll('.bar-pill').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const type = e.currentTarget.dataset.type;
            activateCategory(type);
        });
    });

    document.getElementById('exploreBtn')?.addEventListener('click', openShowcase);
    document.getElementById('showFeaturesBtn')?.addEventListener('click', openShowcase);
}

// Central function to activate a category and sync both pill sets
function activateCategory(type) {
    // Sync welcome-screen pills
    document.querySelectorAll('.cat-pill').forEach(p => {
        const match = p.dataset.type === type;
        p.classList.toggle('active', match);
        p.setAttribute('aria-pressed', match ? 'true' : 'false');
        if (match) {
            const icon = p.querySelector('.cat-icon');
            if (icon) { icon.style.animation = 'none'; icon.offsetHeight; icon.style.animation = ''; }
        }
    });
    // Sync header bar pills
    document.querySelectorAll('.bar-pill').forEach(p => {
        const match = p.dataset.type === type;
        p.classList.toggle('active', match);
        p.setAttribute('aria-pressed', match ? 'true' : 'false');
    });
    requestType = type;
    document.getElementById('currentCategoryText').textContent = type;
    if (FLOWS[type]) startFlow(type);
    else flowStep = -1;
}

function sendMessage() {
    const input = document.getElementById('chatInput');
    const msg = input.value.trim();
    if (msg) { input.value = ''; handleUserInput(msg, msg); }
}

function resetChat() {
    currentThreadId = null;
    flowStep = -1;
    flowFormData = {};
    document.getElementById('chatHistory').innerHTML = '';
    document.getElementById('welcomeScreen').classList.remove('hidden');
    document.querySelectorAll('.cat-pill').forEach((b,i) => {
        b.classList.toggle('active', i === 0);
        b.setAttribute('aria-pressed', i === 0 ? 'true' : 'false');
    });
    requestType = 'Any Query';
    document.getElementById('currentCategoryText').textContent = 'Any Query';
}

/* ── FLOW ───────────────────────────────────────────────── */
function startFlow(type) {
    flowStep = 0;
    flowFormData = {};
    document.getElementById('welcomeScreen').classList.add('hidden');
    document.getElementById('chatHistory').innerHTML = '';
    const flow = FLOWS[type];
    const qInfo = flow.questions[0];
    appendMessage('assistant', `I'll help you with <strong>${type}</strong>. Let's get started!\n\n${qInfo.q}`, qInfo.options, qInfo.inputType);
}

async function handleGoBack() {
    document.querySelectorAll('.options-container').forEach(el => el.remove());
    if (flowStep > 0) {
        flowStep--;
        appendMessage('user', '← Back');
        const qInfo = FLOWS[requestType].questions[flowStep];
        appendMessage('assistant', `No problem, let's redo that.\n\n${qInfo.q}`, qInfo.options, qInfo.inputType);
    }
}

async function handleUserInput(msgValue, displayMsg) {
    appendMessage('user', displayMsg);
    document.getElementById('welcomeScreen').classList.add('hidden');
    document.querySelectorAll('.options-container').forEach(el => el.remove());

    const activeFlow = FLOWS[requestType];
    if (activeFlow && flowStep >= 0) {
        const currentQ = activeFlow.questions[flowStep];
        let valType = 'text';
        if (currentQ.key.toLowerCase().includes('email')) valType = 'email';
        else if (currentQ.key.toLowerCase().includes('empid') || currentQ.key === 'EmployeeId') valType = 'employeeId';
        else if (currentQ.inputType === 'date') valType = 'date';

        const v = validateInput(msgValue, valType);
        if (!v.valid) {
            showError(v.message);
            appendMessage('assistant', `⚠️ ${v.message}`);
            return;
        }

        flowFormData[activeFlow.questions[flowStep].key] = msgValue;
        flowStep++;

        if (flowStep < activeFlow.questions.length) {
            const qInfo = activeFlow.questions[flowStep];
            appendMessage('assistant', qInfo.q, qInfo.options, qInfo.inputType);
        } else {
            appendMessage('assistant', "Almost done — submitting your application…");
            await submitFlow(requestType);
            flowStep = -1;
        }
        return;
    }

    try {
        showLoading('Getting response…');
        const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ thread_id: currentThreadId, message: msgValue, request_type: requestType })
        });
        if (!res.ok) throw new Error(res.status === 429 ? 'Too many requests. Please wait a moment.' : 'Failed to get response.');
        const data = await res.json();
        currentThreadId = data.thread_id;
        appendMessage('assistant', data.response);
        if (data.sources?.length > 0) {
            appendMessage('assistant', '📄 Sources:<br>' + data.sources.join('<br>'));
        }
        await loadConversations();
    } catch (err) {
        console.error('Chat error:', err);
        showError(err.message || 'Failed to send message. Please try again.');
        appendMessage('assistant', '⚠️ I encountered an error. Please try again.');
    } finally {
        hideLoading();
    }
}

async function submitFlow(type) {
    const flow = FLOWS[type];
    try {
        showLoading('Submitting application…');
        const formData = await flow.formatData(flowFormData);
        const res = await fetch(flow.endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        if (!res.ok) throw new Error('Failed to submit application.');
        const data = await res.json();
        currentThreadId = data.thread_id;
        appendMessage('assistant', `✅ ${flow.successMsg}\n\n${flow.formatSummary(formData)}`);
        showSuccess(flow.successMsg);
        setTimeout(() => {
            const followUp = {
                'Apply WFH': 'Your WFH request is submitted. You\'ll receive an email confirmation within 24 hours. Need anything else?',
                'IT Ticket Raised': 'Your IT ticket is submitted. Our team will respond within 24 hours. Anything else I can help with?',
                'Leave Apply': 'Your leave application is submitted. You\'ll receive an email confirmation shortly. Anything else?'
            }[type] || 'Anything else I can help you with today?';
            appendMessage('assistant', followUp);
        }, 800);
        await loadConversations();
    } catch (err) {
        console.error('Submit error:', err);
        showError('Failed to submit application. Please try again.');
        appendMessage('assistant', '⚠️ There was an error submitting your application. Please try again.');
    } finally {
        hideLoading();
    }
}

/* ── MESSAGE RENDERING ──────────────────────────────────── */
function appendMessage(role, text, options = null, inputType = null) {
    const chatHistory = document.getElementById('chatHistory');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = text.replace(/\n/g, '<br>');
    chatHistory.appendChild(div);

    if (role === 'assistant') {
        const flowDef = FLOWS[requestType];
        const isWizard = (flowDef && flowStep > 0 && flowStep < flowDef.questions.length);

        if (options) {
            const optionsDiv = document.createElement('div');
            optionsDiv.className = 'options-container';
            options.forEach(opt => {
                const btn = document.createElement('button');
                btn.className = 'option-btn';
                btn.textContent = opt.label;
                btn.onclick = () => handleUserInput(opt.value, opt.label);
                optionsDiv.appendChild(btn);
            });
            if (isWizard) {
                const backBtn = document.createElement('button');
                backBtn.className = 'option-btn secondary-btn';
                backBtn.textContent = '← Back';
                backBtn.onclick = handleGoBack;
                optionsDiv.appendChild(backBtn);
            }
            chatHistory.appendChild(optionsDiv);
        } else if (inputType === 'date') {
            const optionsDiv = document.createElement('div');
            optionsDiv.className = 'options-container';
            const dateInput = document.createElement('input');
            dateInput.type = 'date';
            dateInput.className = 'date-picker-input';
            const today = new Date(); today.setHours(0,0,0,0);
            dateInput.min = today.toISOString().split('T')[0];
            const btn = document.createElement('button');
            btn.className = 'option-btn primary-btn';
            btn.textContent = 'Confirm Date';
            btn.onclick = () => {
                if (dateInput.value) handleUserInput(dateInput.value, dateInput.value);
                else showError("Please select a date first.");
            };
            optionsDiv.appendChild(dateInput);
            optionsDiv.appendChild(btn);
            if (isWizard) {
                const backBtn = document.createElement('button');
                backBtn.className = 'option-btn secondary-btn';
                backBtn.textContent = '← Back';
                backBtn.onclick = handleGoBack;
                optionsDiv.appendChild(backBtn);
            }
            chatHistory.appendChild(optionsDiv);
        } else if (inputType === 'file') {
            const optionsDiv = document.createElement('div');
            optionsDiv.className = 'options-container';
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.className = 'file-picker-input';
            const btn = document.createElement('button');
            btn.className = 'option-btn primary-btn';
            btn.textContent = 'Upload & Continue';
            const skipBtn = document.createElement('button');
            skipBtn.className = 'option-btn secondary-btn';
            skipBtn.textContent = 'Skip';
            skipBtn.onclick = () => handleUserInput('NA', 'No attachment');
            btn.onclick = async () => {
                if (!fileInput.files.length) { showError("Please select a file or click Skip."); return; }
                const file = fileInput.files[0];
                const formData = new FormData();
                formData.append('file', file);
                btn.textContent = 'Uploading…';
                btn.disabled = true;
                try {
                    const res = await fetch('/upload_file', { method: 'POST', body: formData });
                    const data = await res.json();
                    handleUserInput(data.path, `Attached: ${file.name}`);
                } catch {
                    showError("Upload failed. Please try again.");
                    btn.textContent = 'Upload & Continue';
                    btn.disabled = false;
                }
            };
            optionsDiv.appendChild(fileInput);
            optionsDiv.appendChild(btn);
            optionsDiv.appendChild(skipBtn);
            if (isWizard) {
                const backBtn = document.createElement('button');
                backBtn.className = 'option-btn secondary-btn';
                backBtn.textContent = '← Back';
                backBtn.onclick = handleGoBack;
                optionsDiv.appendChild(backBtn);
            }
            chatHistory.appendChild(optionsDiv);
        } else if (isWizard) {
            const optionsDiv = document.createElement('div');
            optionsDiv.className = 'options-container';
            const backBtn = document.createElement('button');
            backBtn.className = 'option-btn secondary-btn';
            backBtn.textContent = '← Back';
            backBtn.onclick = handleGoBack;
            optionsDiv.appendChild(backBtn);
            chatHistory.appendChild(optionsDiv);
        }
    }

    div.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

/* ── CONVERSATIONS ──────────────────────────────────────── */
async function loadConversations() {
    try {
        const res = await fetch('/conversations');
        if (!res.ok) throw new Error();
        const convos = await res.json();
        const list = document.getElementById('conversationsList');
        list.innerHTML = '';
        if (!convos.length) {
            const empty = document.createElement('div');
            empty.style.cssText = 'text-align:center;color:#8888aa;padding:16px;font-size:0.8rem;';
            empty.textContent = 'No conversations yet';
            list.appendChild(empty);
            return;
        }
        convos.forEach(c => {
            const btn = document.createElement('button');
            btn.className = 'convo-btn' + (c.thread_id === currentThreadId ? ' active' : '');
            btn.textContent = c.title || 'Untitled Conversation';
            btn.setAttribute('role', 'listitem');
            btn.onclick = () => loadChat(c.thread_id);
            list.appendChild(btn);
        });
    } catch {
        console.error('Failed to load conversations');
    }
}

async function loadChat(threadId) {
    try {
        showLoading('Loading conversation…');
        currentThreadId = threadId;
        flowStep = -1;
        document.getElementById('welcomeScreen').classList.add('hidden');
        const res = await fetch(`/conversations/${threadId}/messages`);
        if (!res.ok) throw new Error();
        const msgs = await res.json();
        const history = document.getElementById('chatHistory');
        history.innerHTML = '';
        if (!msgs.length) {
            const empty = document.createElement('div');
            empty.style.cssText = 'text-align:center;color:#8888aa;padding:40px;font-style:italic;';
            empty.textContent = 'No messages in this conversation';
            history.appendChild(empty);
        } else {
            msgs.forEach(m => {
                if (m.user_message) appendMessage('user', m.user_message);
                if (m.assistant_message) appendMessage('assistant', m.assistant_message);
            });
        }
        await loadConversations();
    } catch {
        showError('Failed to load conversation. Please try again.');
    } finally {
        hideLoading();
    }
}

/* ── PDF UPLOAD ─────────────────────────────────────────── */
async function uploadPdf() {
    const fileNode = document.getElementById('pdfUpload');
    const statusDiv = document.getElementById('uploadStatus');
    if (!fileNode.files.length) { showError('Please select a PDF file first.'); return; }
    const file = fileNode.files[0];
    if (file.type !== 'application/pdf') { showError('Please select a valid PDF file.'); return; }
    if (file.size > 10 * 1024 * 1024) { showError('File size must be less than 10MB.'); return; }
    const formData = new FormData();
    formData.append('file', file);
    statusDiv.textContent = 'Uploading…';
    statusDiv.style.color = '#7c6fff';
    try {
        const res = await fetch('/upload_pdf', { method: 'POST', body: formData });
        if (!res.ok) throw new Error();
        const data = await res.json();
        statusDiv.textContent = data.message || '✓ Upload successful!';
        statusDiv.style.color = '#00c896';
        showSuccess('PDF uploaded successfully!');
        fileNode.value = '';
        setTimeout(() => { statusDiv.textContent = ''; }, 5000);
    } catch {
        statusDiv.textContent = '✗ Upload failed. Please try again.';
        statusDiv.style.color = '#ff4d6a';
        showError('Failed to upload PDF. Please try again.');
    }
}

/* ── DRAG & DROP ────────────────────────────────────────── */
function setupDragDrop() {
    const zone = document.getElementById('uploadZone');
    if (!zone) return;
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.style.borderColor = 'var(--accent)'; });
    zone.addEventListener('dragleave', () => { zone.style.borderColor = ''; });
    zone.addEventListener('drop', e => {
        e.preventDefault();
        zone.style.borderColor = '';
        const file = e.dataTransfer.files[0];
        if (file?.type === 'application/pdf') {
            const input = document.getElementById('pdfUpload');
            const dt = new DataTransfer();
            dt.items.add(file);
            input.files = dt.files;
            document.getElementById('uploadStatus').textContent = `Selected: ${file.name}`;
        } else {
            showError('Only PDF files are accepted.');
        }
    });
    zone.addEventListener('click', () => document.getElementById('pdfUpload').click());
}

/* ── FEATURE SHOWCASE ───────────────────────────────────── */
let showcaseIndex = 0;
const FEATURE_COUNT = 5;

function setupShowcase() {
    // Build dots
    const dotsContainer = document.getElementById('showcaseDots');
    for (let i = 0; i < FEATURE_COUNT; i++) {
        const dot = document.createElement('div');
        dot.className = 'dot' + (i === 0 ? ' active' : '');
        dot.onclick = () => goToCard(i);
        dotsContainer.appendChild(dot);
    }

    document.getElementById('prevCard').addEventListener('click', () => goToCard(showcaseIndex - 1));
    document.getElementById('nextCard').addEventListener('click', () => goToCard(showcaseIndex + 1));
    document.getElementById('closeShowcase').addEventListener('click', closeShowcase);

    // Close on backdrop click
    document.getElementById('featureShowcase').addEventListener('click', (e) => {
        if (e.target === document.getElementById('featureShowcase')) closeShowcase();
    });

    // Close on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeShowcase();
        if (e.key === 'ArrowRight' && !document.getElementById('featureShowcase').classList.contains('hidden'))
            goToCard(showcaseIndex + 1);
        if (e.key === 'ArrowLeft' && !document.getElementById('featureShowcase').classList.contains('hidden'))
            goToCard(showcaseIndex - 1);
    });

    // "Try it" buttons AND full card click
    document.querySelectorAll('.feature-card').forEach(card => {
        const type = card.querySelector('.feature-try-btn')?.dataset.type;
        if (!type) return;

        const activate = () => {
            card.classList.add('selected');
            setTimeout(() => card.classList.remove('selected'), 300);
            closeShowcase();
            activateCategory(type);
        };

        card.addEventListener('click', activate);
        card.setAttribute('role', 'button');
        card.setAttribute('tabindex', '0');
        card.setAttribute('aria-label', `Try ${type}`);
        card.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); activate(); } });
    });

    // Keep standalone try buttons working too (they're inside cards, clicks bubble up — no duplicate needed)
    document.querySelectorAll('.feature-try-btn').forEach(btn => {
        btn.addEventListener('click', e => e.stopPropagation()); // card handler does the work
    });

    // Touch/swipe support
    const track = document.getElementById('showcaseTrack');
    let touchStartX = 0;
    track.addEventListener('touchstart', e => { touchStartX = e.touches[0].clientX; }, { passive: true });
    track.addEventListener('touchend', e => {
        const dx = touchStartX - e.changedTouches[0].clientX;
        if (Math.abs(dx) > 40) goToCard(showcaseIndex + (dx > 0 ? 1 : -1));
    }, { passive: true });
}

function goToCard(index) {
    showcaseIndex = Math.max(0, Math.min(FEATURE_COUNT - 1, index));
    const track = document.getElementById('showcaseTrack');
    const cardWidth = track.parentElement.clientWidth;
    track.style.transform = `translateX(-${showcaseIndex * (cardWidth + 20)}px)`;
    document.querySelectorAll('.dot').forEach((d, i) => d.classList.toggle('active', i === showcaseIndex));
}

function openShowcase() {
    showcaseIndex = 0;
    document.getElementById('featureShowcase').classList.remove('hidden');
    // Reset track position after DOM is visible
    requestAnimationFrame(() => {
        const track = document.getElementById('showcaseTrack');
        track.style.transform = 'translateX(0)';
        document.querySelectorAll('.dot').forEach((d, i) => d.classList.toggle('active', i === 0));
    });
}

function closeShowcase() {
    document.getElementById('featureShowcase').classList.add('hidden');
}