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
});

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
        if (e.key === 'Enter') {
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
            document.querySelectorAll('.pill').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
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
    const res = await fetch('/conversations');
    const convos = await res.json();
    const list = document.getElementById('conversationsList');
    list.innerHTML = '';
    convos.forEach(c => {
        const btn = document.createElement('button');
        btn.className = 'convo-btn' + (c.thread_id === currentThreadId ? ' active' : '');
        btn.textContent = c.title;
        btn.onclick = () => loadChat(c.thread_id);
        list.appendChild(btn);
    });
}

async function loadChat(threadId) {
    currentThreadId = threadId;
    flowStep = -1;
    document.getElementById('welcomeScreen').classList.add('hidden');
    const res = await fetch(`/conversations/${threadId}/messages`);
    const msgs = await res.json();

    const history = document.getElementById('chatHistory');
    history.innerHTML = '';
    msgs.forEach(m => {
        appendMessage('user', m.user_message);
        appendMessage('assistant', m.assistant_message);
    });
    loadConversations();
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

            const btn = document.createElement('button');
            btn.className = 'option-btn primary-btn';
            btn.textContent = 'Submit Date';
            btn.onclick = () => {
                if (dateInput.value) {
                    handleUserInput(dateInput.value, dateInput.value);
                } else {
                    alert("Please select a date first.");
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
        // Collect data
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

    // Normal chat
    const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            thread_id: currentThreadId,
            message: msgValue,
            request_type: requestType
        })
    });
    const data = await res.json();
    currentThreadId = data.thread_id;
    appendMessage('assistant', data.response);
    if (data.sources && data.sources.length > 0) {
        appendMessage('assistant', 'Sources:<br>' + data.sources.join('<br>'));
    }
    loadConversations();
}

async function submitFlow(type) {
    const flow = FLOWS[type];
    const formData = await flow.formatData(flowFormData);

    try {
        const res = await fetch(flow.endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        const data = await res.json();
        currentThreadId = data.thread_id;

        const summaryMsg = `${flow.successMsg}\n\nCollected Data:\n` + flow.formatSummary(formData);

        appendMessage('assistant', summaryMsg);
        loadConversations();
    } catch (e) {
        appendMessage('assistant', 'Failed to submit application. Please try again.');
    }
}

async function uploadPdf() {
    const fileNode = document.getElementById('pdfUpload');
    if (!fileNode.files.length) return;
    const file = fileNode.files[0];
    const formData = new FormData();
    formData.append('file', file);

    document.getElementById('uploadStatus').textContent = 'Uploading...';
    try {
        const res = await fetch('/upload_pdf', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        document.getElementById('uploadStatus').textContent = data.message;
    } catch (e) {
        document.getElementById('uploadStatus').textContent = 'Error uploading';
    }
}
