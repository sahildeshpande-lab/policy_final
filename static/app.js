let currentThreadId = null;
let requestType = "Any Query";

let flowFormData = {};
let flowStep = -1;

const FLOWS = {
    "Leave Apply": {
        endpoint: "/leave_apply",
        successMsg: "Leave application submitted successfully!",
        questions: [
            { key: "name", q: "What is your Name?" },
            { key: "empId", q: "What is your Employee ID?" },
            {
                key: "leaveGrade",
                q: "What is your Leave Grade?",
                options: [
                    { value: "1", label: "Planned Leave (PLY)" },
                    { value: "2", label: "Leave Intimation (Already Taken)" }
                ]
            },
            { key: "leaveStartDate", q: "What is the Leave Start Date?", inputType: "date" },
            { key: "leaveEndDate", q: "What is the Leave End Date?", inputType: "date" },
            {
                key: "leaveType",
                q: "What is the Leave Type?",
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
                q: "What is the Leave Category?",
                options: [
                    { value: "1", label: "Sick Leave" },
                    { value: "2", label: "Casual Leave" },
                    { value: "3", label: "Complementary Leave" }
                ]
            },
            { key: "leaveContent", q: "Please provide the Reason/Comments for your leave:" },
            { key: "managerId", q: "What is your Manager's ID?" }
        ],
        formatData: async (fd) => {
            const rawSalt = `${Date.now()}_${fd.name}_${fd.empId}_${fd.managerId}`;
            const encoder = new TextEncoder();
            const data = encoder.encode(rawSalt);
            const hashBuffer = await crypto.subtle.digest('SHA-256', data);
            const hashArray = Array.from(new Uint8Array(hashBuffer));
            const salt = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

            return {
                name: fd.name,
                empId: fd.empId,
                leaveGrade: parseInt(fd.leaveGrade) || 1,
                leaveStartDate: fd.leaveStartDate,
                leaveEndDate: fd.leaveEndDate,
                leaveType: parseInt(fd.leaveType) || 0,
                leaveCategory: parseInt(fd.leaveCategory) || 1,
                leaveContent: fd.leaveContent,
                managerId: fd.managerId,
                salt: salt,
                thread_id: currentThreadId
            };
        },
        formatSummary: (fd) => (
            `- Name: ${fd.name}\n` +
            `- Employee ID: ${fd.empId}\n` +
            `- Manager ID: ${fd.managerId}\n` +
            `- Leave Grade: ${fd.leaveGrade}\n` +
            `- Leave Type: ${fd.leaveType}\n` +
            `- Leave Category: ${fd.leaveCategory}\n` +
            `- Dates: ${fd.leaveStartDate} to ${fd.leaveEndDate}\n` +
            `- Reason: ${fd.leaveContent}\n` +
            `- Approval Salt: ${fd.salt}`
        )
    },
    "Apply WFH": {
        endpoint: "/wfh_apply",
        successMsg: "WFH application submitted successfully!",
        questions: [
            { key: "empId", q: "What is your Employee ID?" },
            {
                key: "is_extra_request",
                q: "Is this a Normal WFH Request or an Extra WFH Request (exceeding monthly quota)?",
                options: [
                    { value: "0", label: "Normal (Within Quota)" },
                    { value: "1", label: "Extra (Exceeded Quota)" }
                ]
            },
            { key: "wfhStartDate", q: "When does your WFH start?", inputType: "date" },
            { key: "wfhEndDate", q: "When does your WFH end?", inputType: "date" },
            {
                key: "reason",
                q: "For Extra WFH Requests, please provide a mandatory reason (If Normal, you can type 'NA' or a brief reason):"
            },
            { key: "managerId", q: "What is your Manager's ID?" }
        ],
        formatData: (fd) => ({
            empId: fd.empId,
            wfhStartDate: fd.wfhStartDate,
            wfhEndDate: fd.wfhEndDate,
            reason: fd.reason,
            is_extra_request: parseInt(fd.is_extra_request) || 0,
            managerId: fd.managerId,
            thread_id: currentThreadId
        }),
        formatSummary: (fd) => {
            const reqTypeStr = fd.is_extra_request ? "Extra WFH Request (Pending HR)" : "Normal WFH Request (Pending Manager)";
            return `- Employee ID: ${fd.empId}\n` +
                `- Manager ID: ${fd.managerId}\n` +
                `- Request Type: ${reqTypeStr}\n` +
                `- Dates: ${fd.wfhStartDate} to ${fd.wfhEndDate}\n` +
                `- Reason: ${fd.reason}`
        }
    },
    "IT Ticket Raised": {
        endpoint: "/it_ticket_apply",
        successMsg: "IT/Helpdesk ticket submitted successfully!",
        questions: [
            { key: "EmployeeId", q: "What is your Employee ID? (e.g. SOLxxx)" },
            { key: "managerId", q: "What is your Manager's ID?" },
            {
                key: "category_id",
                q: "What category best describes your issue?",
                options: [
                    { value: "4", label: "Machine Performance" },
                    { value: "5", label: "Information Security" },
                    { value: "7", label: "Hardware Support" },
                    { value: "8", label: "Application Support" },
                    { value: "10", label: "Other IT" },
                    { value: "11", label: "HR - Documents" },
                    { value: "12", label: "HR - Other" },
                    { value: "9", label: "Request For IT Peripherals" },
                    { value: "0", label: "Other Unlisted Category" }
                ]
            },
            { key: "title", q: "Briefly, what is the title or subject of your issue?" },
            { key: "description", q: "Please provide a detailed explanation of your problem:" },
            { key: "attachment", q: "Attach any image or document related to the issue:", inputType: "file" },
        ],
        formatData: (fd) => ({
            EmployeeId: fd.EmployeeId,
            category_id: parseInt(fd.category_id) || 0,
            title: fd.title,
            description: fd.description,
            attachment: fd.attachment === 'NA' ? '' : fd.attachment,
            managerId: fd.managerId,
            thread_id: currentThreadId
        }),
        formatSummary: (fd) => {
            const tempItCats = [4, 5, 6, 7, 8, 10];
            const tempHrCats = [11, 12];
            let emailRoute = `${fd.managerId}@company.com`;
            let deptRoute = 'Direct Manager';
            if (tempItCats.includes(fd.category_id)) {
                emailRoute = 'teamit@solacetechnologies.co.in';
                deptRoute = 'IT Department';
            } else if (tempHrCats.includes(fd.category_id)) {
                emailRoute = 'hr.mgr@solacetechnologies.co.in';
                deptRoute = 'HR Department';
            }

            return `- Employee ID: ${fd.EmployeeId}\n` +
                `- Manager ID: ${fd.managerId}\n` +
                `- Category ID: ${fd.category_id}\n` +
                `- Title: ${fd.title}\n` +
                `- Description: ${fd.description}\n` +
                `- Attachment: ${fd.attachment ? fd.attachment : 'None'}\n` +
                `- Routed To: ${deptRoute} (${emailRoute})`;
        }
    }
};

document.addEventListener("DOMContentLoaded", () => {
    loadConversations();
    setupEventListeners();
    setupErrorHandling();
});

function showLoading(message = "Processing...") {
    const overlay = document.getElementById('loadingOverlay');
    const loadingText = overlay.querySelector('.loading-text');
    loadingText.textContent = message;
    overlay.classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden');
}

function showError(message) {
    const toast = document.getElementById('errorToast');
    const errorMessage = toast.querySelector('.error-message');
    errorMessage.textContent = message;
    toast.classList.remove('hidden');
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 5000);
}

function setupErrorHandling() {
    const errorClose = document.querySelector('.error-close');
    errorClose.addEventListener('click', () => {
        document.getElementById('errorToast').classList.add('hidden');
    });
    
    window.addEventListener('unhandledrejection', (event) => {
        showError('An unexpected error occurred. Please try again.');
        console.error('Unhandled promise rejection:', event.reason);
    });
    
    window.addEventListener('error', (event) => {
        showError('An unexpected error occurred. Please try again.');
        console.error('Global error:', event.error);
    });
}

function validateInput(value, type = 'text') {
    if (!value || value.trim() === '') {
        return { valid: false, message: 'This field is required' };
    }
    
    if (type === 'email') {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            return { valid: false, message: 'Please enter a valid email address' };
        }
    }
    
    if (type === 'employeeId') {
        if (!/^SOL\d+/i.test(value)) {
            return { valid: false, message: 'Employee ID should start with SOL followed by numbers' };
        }
    }
    
    if (type === 'date') {
        const selectedDate = new Date(value);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        if (selectedDate < today) {
            return { valid: false, message: 'Date cannot be in the past' };
        }
    }
    
    return { valid: true };
}

function setupEventListeners() {
    document.getElementById('uploadBtn').addEventListener('click', uploadPdf);
    document.getElementById('newChatBtn').addEventListener('click', () => {
        currentThreadId = null;
        flowStep = -1;
        document.getElementById('chatHistory').innerHTML = '';
        document.getElementById('welcomeScreen').classList.remove('hidden');
    });

    document.getElementById('sendBtn').addEventListener('click', () => {
        const input = document.getElementById('chatInput');
        const msg = input.value.trim();
        if (msg) {
            input.value = '';
            handleUserInput(msg, msg);
        }
    });

    document.getElementById('chatInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            const input = document.getElementById('chatInput');
            const msg = input.value.trim();
            if (msg) {
                input.value = '';
                handleUserInput(msg, msg);
            }
        }
    });

    document.querySelectorAll('.pill').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.pill').forEach(b => {
                b.classList.remove('active');
                b.setAttribute('aria-pressed', 'false');
            });
            e.target.classList.add('active');
            e.target.setAttribute('aria-pressed', 'true');
            requestType = e.target.dataset.type;
            document.getElementById('currentCategoryText').textContent = requestType;

            if (FLOWS[requestType]) {
                startFlow(requestType);
            } else {
                flowStep = -1;
            }
        });
    });
}

function startFlow(type) {
    flowStep = 0;
    flowFormData = {};
    document.getElementById('welcomeScreen').classList.add('hidden');
    document.getElementById('chatHistory').innerHTML = '';

    const flow = FLOWS[type];
    const qInfo = flow.questions[0];

    appendMessage('assistant', `I will help you with ${type}. Let's start.\n\n` + qInfo.q, qInfo.options, qInfo.inputType);
}

async function loadConversations() {
    try {
        const res = await fetch('/conversations');
        if (!res.ok) throw new Error('Failed to load conversations');
        const convos = await res.json();
        const list = document.getElementById('conversationsList');
        list.innerHTML = '';
        
        if (convos.length === 0) {
            const emptyMsg = document.createElement('div');
            emptyMsg.className = 'empty-conversations';
            emptyMsg.textContent = 'No conversations yet';
            emptyMsg.style.cssText = 'text-align: center; color: #64748b; padding: 20px; font-size: 0.875rem;';
            list.appendChild(emptyMsg);
            return;
        }
        
        convos.forEach(c => {
            const btn = document.createElement('button');
            btn.className = 'convo-btn' + (c.thread_id === currentThreadId ? ' active' : '');
            btn.textContent = c.title || 'Untitled Conversation';
            btn.onclick = () => loadChat(c.thread_id);
            list.appendChild(btn);
        });
    } catch (error) {
        console.error('Error loading conversations:', error);
        showError('Failed to load conversations. Please refresh the page.');
    }
}

async function loadChat(threadId) {
    try {
        showLoading('Loading conversation...');
        currentThreadId = threadId;
        flowStep = -1;
        document.getElementById('welcomeScreen').classList.add('hidden');
        
        const res = await fetch(`/conversations/${threadId}/messages`);
        if (!res.ok) throw new Error('Failed to load conversation');
        const msgs = await res.json();

        const history = document.getElementById('chatHistory');
        history.innerHTML = '';
        
        if (msgs.length === 0) {
            const emptyMsg = document.createElement('div');
            emptyMsg.className = 'empty-messages';
            emptyMsg.textContent = 'No messages in this conversation';
            emptyMsg.style.cssText = 'text-align: center; color: #64748b; padding: 40px; font-style: italic;';
            history.appendChild(emptyMsg);
        } else {
            msgs.forEach(m => {
                if (m.user_message) {
                    appendMessage('user', m.user_message);
                }
                if (m.assistant_message) {
                    appendMessage('assistant', m.assistant_message);
                }
            });
        }
        
        await loadConversations();
    } catch (error) {
        console.error('Error loading chat:', error);
        showError('Failed to load conversation. Please try again.');
    } finally {
        hideLoading();
    }
}

function appendMessage(role, text, options = null, inputType = null) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = text.replace(/\n/g, '<br>');
    document.getElementById('chatHistory').appendChild(div);

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
                backBtn.textContent = '⬅️ Back';
                backBtn.onclick = () => handleGoBack();
                optionsDiv.appendChild(backBtn);
            }

            document.getElementById('chatHistory').appendChild(optionsDiv);
        } else if (inputType === 'date') {
            const optionsDiv = document.createElement('div');
            optionsDiv.className = 'options-container';

            const dateInput = document.createElement('input');
            dateInput.type = 'date';
            dateInput.className = 'date-picker-input';
            
            // Set minimum date to today to prevent past dates
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            dateInput.min = today.toISOString().split('T')[0];

            const btn = document.createElement('button');
            btn.className = 'option-btn primary-btn';
            btn.textContent = 'Submit Date';
            btn.onclick = () => {
                if (dateInput.value) {
                    handleUserInput(dateInput.value, dateInput.value);
                } else {
                    showError("Please select a date first.");
                }
            };

            optionsDiv.appendChild(dateInput);
            optionsDiv.appendChild(btn);

            if (isWizard) {
                const backBtn = document.createElement('button');
                backBtn.className = 'option-btn secondary-btn';
                backBtn.textContent = '⬅️ Back';
                backBtn.onclick = () => handleGoBack();
                optionsDiv.appendChild(backBtn);
            }

            document.getElementById('chatHistory').appendChild(optionsDiv);
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
                if (fileInput.files.length > 0) {
                    const file = fileInput.files[0];
                    const formData = new FormData();
                    formData.append('file', file);
                    btn.textContent = 'Uploading...';
                    btn.disabled = true;

                    try {
                        const res = await fetch('/upload_file', {
                            method: 'POST',
                            body: formData
                        });
                        const data = await res.json();
                        handleUserInput(data.path, `Attached: ${file.name}`);
                    } catch (e) {
                        alert("Upload failed.");
                        btn.textContent = 'Upload & Continue';
                        btn.disabled = false;
                    }
                } else {
                    alert("Please select a file or click Skip.");
                }
            };

            optionsDiv.appendChild(fileInput);
            optionsDiv.appendChild(btn);
            optionsDiv.appendChild(skipBtn);

            if (isWizard) {
                const backBtn = document.createElement('button');
                backBtn.className = 'option-btn secondary-btn';
                backBtn.textContent = '⬅️ Back';
                backBtn.onclick = () => handleGoBack();
                optionsDiv.appendChild(backBtn);
            }

            document.getElementById('chatHistory').appendChild(optionsDiv);
        } else if (isWizard) {
            const optionsDiv = document.createElement('div');
            optionsDiv.className = 'options-container';
            const backBtn = document.createElement('button');
            backBtn.className = 'option-btn secondary-btn';
            backBtn.textContent = '⬅️ Back';
            backBtn.onclick = () => handleGoBack();
            optionsDiv.appendChild(backBtn);
            document.getElementById('chatHistory').appendChild(optionsDiv);
        }
    }

    div.scrollIntoView();
}

async function handleGoBack() {
    document.querySelectorAll('.options-container').forEach(el => el.remove());
    if (flowStep > 0) {
        flowStep--;
        appendMessage('user', '⬅️ Back');
        const qInfo = FLOWS[requestType].questions[flowStep];
        appendMessage('assistant', "Let's try that again. " + qInfo.q, qInfo.options, qInfo.inputType);
    }
}

async function handleUserInput(msgValue, displayMsg) {
    appendMessage('user', displayMsg);
    document.getElementById('welcomeScreen').classList.add('hidden');

    document.querySelectorAll('.options-container').forEach(el => el.remove());

    const activeFlow = FLOWS[requestType];

    if (activeFlow && flowStep >= 0) {
        const currentQuestion = activeFlow.questions[flowStep];
        let validationType = 'text';
        
        if (currentQuestion.key.toLowerCase().includes('email')) {
            validationType = 'email';
        } else if (currentQuestion.key.toLowerCase().includes('empid') || currentQuestion.key === 'EmployeeId') {
            validationType = 'employeeId';
        } else if (currentQuestion.inputType === 'date') {
            validationType = 'date';
        }
        
        const validation = validateInput(msgValue, validationType);
        if (!validation.valid) {
            showError(validation.message);
            appendMessage('assistant', `Please correct the following issue: ${validation.message}`);
            return;
        }
        
        flowFormData[activeFlow.questions[flowStep].key] = msgValue;
        flowStep++;

        if (flowStep < activeFlow.questions.length) {
            const qInfo = activeFlow.questions[flowStep];
            appendMessage('assistant', qInfo.q, qInfo.options, qInfo.inputType);
        } else {
            appendMessage('assistant', "Thank you. Submitting your application...");
            await submitFlow(requestType);
            flowStep = -1;
        }
        return;
    }

    try {
        showLoading('Getting response...');
        
        const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                thread_id: currentThreadId,
                message: msgValue,
                request_type: requestType
            })
        });
        
        if (!res.ok) {
            throw new Error(res.status === 429 ? 'Too many requests. Please wait a moment.' : 'Failed to get response');
        }
        
        const data = await res.json();
        currentThreadId = data.thread_id;
        appendMessage('assistant', data.response);
        
        if (data.sources && data.sources.length > 0) {
            appendMessage('assistant', 'Sources:<br>' + data.sources.join('<br>'));
        }
        
        await loadConversations();
    } catch (error) {
        console.error('Error in chat:', error);
        showError(error.message || 'Failed to send message. Please try again.');
        appendMessage('assistant', 'I apologize, but I encountered an error. Please try again.');
    } finally {
        hideLoading();
    }
}

async function submitFlow(type) {
    const flow = FLOWS[type];
    
    try {
        showLoading('Submitting application...');
        const formData = await flow.formatData(flowFormData);

        const res = await fetch(flow.endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        if (!res.ok) {
            throw new Error('Failed to submit application');
        }
        
        const data = await res.json();
        currentThreadId = data.thread_id;

        const summaryMsg = `${flow.successMsg}\n\nCollected Data:\n` + flow.formatSummary(formData);
        appendMessage('assistant', summaryMsg);
        
        // Ask if employee needs help with anything else
        setTimeout(() => {
            if (type === 'Apply WFH') {
                appendMessage('assistant', 'Your WFH request has been submitted. Please note that you will receive an email with the approval status within 24 hours. Is there anything else I can help you with?');
            } else if (type === 'IT Ticket Raised') {
                appendMessage('assistant', 'Your IT ticket has been submitted. Our IT team will review and respond to your request within 24 hours. Is there anything else I can help you with?');
            } else if (type === 'Leave Apply') {
                appendMessage('assistant', 'Your leave application has been submitted successfully. You will receive an email confirmation shortly. Is there anything else I can help you with?');
            } else {
                appendMessage('assistant', 'Is there anything else I can help you with today? You can ask about company policies, apply for WFH, raise IT tickets, or any other queries.');
            }
        }, 1000);
        
        await loadConversations();
    } catch (error) {
        console.error('Error submitting flow:', error);
        showError('Failed to submit application. Please try again.');
        appendMessage('assistant', 'I apologize, but there was an error submitting your application. Please try again.');
    } finally {
        hideLoading();
    }
}

async function uploadPdf() {
    const fileNode = document.getElementById('pdfUpload');
    const statusDiv = document.getElementById('uploadStatus');
    
    if (!fileNode.files.length) {
        showError('Please select a PDF file first');
        return;
    }
    
    const file = fileNode.files[0];
    
    if (file.type !== 'application/pdf') {
        showError('Please select a valid PDF file');
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) { // 10MB limit
        showError('File size must be less than 10MB');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);

    statusDiv.textContent = 'Uploading...';
    statusDiv.style.color = '#3b82f6';
    
    try {
        const res = await fetch('/upload_pdf', {
            method: 'POST',
            body: formData
        });
        
        if (!res.ok) {
            throw new Error('Upload failed');
        }
        
        const data = await res.json();
        statusDiv.textContent = data.message || 'Upload successful!';
        statusDiv.style.color = '#10b981';
        fileNode.value = ''; // Clear file input
        
        // Show success message
        setTimeout(() => {
            statusDiv.textContent = '';
        }, 5000);
        
    } catch (error) {
        console.error('Upload error:', error);
        statusDiv.textContent = 'Upload failed. Please try again.';
        statusDiv.style.color = '#ef4444';
        showError('Failed to upload PDF. Please try again.');
    }
}
