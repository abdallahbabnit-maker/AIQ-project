const API = 'http://127.0.0.1:8000';
let token = null;

// ============ LOGIN ============
const loginForm = document.getElementById('login-form');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        console.log('🔐 محاولة تسجيل الدخول...');
        
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        const errDiv = document.getElementById('login-error');
        
        if (!username || !password) {
            errDiv.textContent = '❌ أدخل اسم المستخدم وكلمة المرور';
            return;
        }
        
        errDiv.textContent = '⏳ جارٍ تسجيل الدخول...';
        
        try {
            const response = await fetch(API + '/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            
            console.log('📡 Response status:', response.status);
            
            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.detail || 'فشل تسجيل الدخول');
            }
            
            const data = await response.json();
            console.log('✅ Login success:', data);
            
            token = data.access_token;
            localStorage.setItem('aiq_token', token);
            localStorage.setItem('aiq_user', username);
            
            errDiv.textContent = '';
            showApp();
            
        } catch (error) {
            console.error('❌ Login error:', error);
            errDiv.textContent = '❌ ' + error.message;
        }
    });
}

function showApp() {
    console.log('🚀 عرض التطبيق الرئيسي');
    document.getElementById('login-screen').classList.remove('active');
    document.getElementById('main-app').classList.add('active');
    
    const username = localStorage.getItem('aiq_user') || 'المؤسس';
    const userNameEl = document.getElementById('user-name');
    if (userNameEl) userNameEl.textContent = username;
    
    loadChat();
}

// ============ LOGOUT ============
const logoutBtn = document.getElementById('logout-btn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        console.log('👋 تسجيل الخروج');
        token = null;
        localStorage.removeItem('aiq_token');
        localStorage.removeItem('aiq_user');
        document.getElementById('main-app').classList.remove('active');
        document.getElementById('login-screen').classList.add('active');
    });
}

// ============ NAVIGATION ============
document.querySelectorAll('.sn').forEach(btn => {
    btn.addEventListener('click', () => {
        console.log('📍 التنقل إلى:', btn.dataset.view);
        
        document.querySelectorAll('.sn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        
        btn.classList.add('active');
        const viewId = 'view-' + btn.dataset.view;
        const viewEl = document.getElementById(viewId);
        if (viewEl) viewEl.classList.add('active');
        
        // تحميل البيانات حسب القسم
        if (btn.dataset.view === 'approvals') loadApprovals();
        if (btn.dataset.view === 'audit') loadAudit();
        if (btn.dataset.view === 'studio') loadStudio();
    });
});

// ============ CHAT ============
function loadChat() {
    console.log('💬 تحميل الشات');
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    
    if (sendBtn) {
        sendBtn.addEventListener('click', () => {
            console.log('📤 إرسال رسالة');
            sendMessage();
        });
    }
    
    if (input) {
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
    
    // اقتراحات
    document.querySelectorAll('.sug').forEach(sug => {
        sug.addEventListener('click', () => {
            console.log('💡 اقتراح:', sug.dataset.q);
            if (input) input.value = sug.dataset.q;
            sendMessage();
        });
    });
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const msgsDiv = document.getElementById('chat-msgs');
    const heroDiv = document.getElementById('chat-hero');
    
    if (!input || !msgsDiv) return;
    
    const text = input.value.trim();
    if (!text) return;
    
    console.log('📝 رسالة:', text);
    
    // إخفاء Hero
    if (heroDiv) heroDiv.style.display = 'none';
    
    // إضافة رسالة المستخدم
    const userMsg = document.createElement('div');
    userMsg.className = 'msg user';
    userMsg.innerHTML = `
        <div class="av">أنا</div>
        <div class="bubble">${text}</div>
    `;
    msgsDiv.appendChild(userMsg);
    
    input.value = '';
    
    // إضافة مؤشر الكتابة
    const typingMsg = document.createElement('div');
    typingMsg.className = 'msg ai';
    typingMsg.innerHTML = `
        <div class="av">AI</div>
        <div class="bubble"><span class="typing"><i></i><i></i><i></i></span></div>
    `;
    msgsDiv.appendChild(typingMsg);
    
    // التمرير للأسفل
    const scrollDiv = document.getElementById('chat-scroll');
    if (scrollDiv) scrollDiv.scrollTop = scrollDiv.scrollHeight;
    
    // إرسال للـ API
    try {
        const response = await fetch(API + '/chat/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ message: text, session_id: 'web' })
        });
        
        console.log('📡 Chat response:', response.status);
        
        typingMsg.remove();
        
        if (!response.ok) {
            throw new Error('فشل الاتصال بالخادم');
        }
        
        const data = await response.json();
        console.log('✅ Reply:', data.reply);
        
        const aiMsg = document.createElement('div');
        aiMsg.className = 'msg ai';
        aiMsg.innerHTML = `
            <div class="av">AI</div>
            <div class="bubble">${data.reply.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')}</div>
        `;
        msgsDiv.appendChild(aiMsg);
        
        if (scrollDiv) scrollDiv.scrollTop = scrollDiv.scrollHeight;
        
    } catch (error) {
        console.error('❌ Chat error:', error);
        typingMsg.remove();
        
        const errorMsg = document.createElement('div');
        errorMsg.className = 'msg ai';
        errorMsg.innerHTML = `
            <div class="av">AI</div>
            <div class="bubble">⚠️ تعذر الاتصال — تأكد أن الخادم يعمل</div>
        `;
        msgsDiv.appendChild(errorMsg);
    }
}

// ============ APPROVALS ============
async function loadApprovals() {
    console.log('✅ تحميل الموافقات');
    const listDiv = document.getElementById('ap-list');
    if (!listDiv) return;
    
    listDiv.innerHTML = '<div class="ap-empty">⏳ جارٍ التحميل...</div>';
    
    try {
        const response = await fetch(API + '/review/pending', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        
        if (!response.ok) throw new Error('فشل التحميل');
        
        const items = await response.json();
        console.log('📋 موافقات معلقة:', items.length);
        
        if (items.length === 0) {
            listDiv.innerHTML = '<div class="ap-empty">✨ لا توجد طلبات — كل شيء تحت السيطرة</div>';
            return;
        }
        
        listDiv.innerHTML = items.map(item => `
            <div class="ap-card">
                <div>
                    <h4>${item.action} <span class="rk ${item.risk}">${item.risk}</span></h4>
                    <p>وكيل: ${item.agent_id} · ${new Date(item.created_at).toLocaleString('ar')}</p>
                </div>
                <div class="ap-btns">
                    <button class="ab ok" onclick="decideApproval('${item.approval_id}', 'approve')">قبول</button>
                    <button class="ab no" onclick="decideApproval('${item.approval_id}', 'reject')">رفض</button>
                    <button class="ab ch" onclick="decideApproval('${item.approval_id}', 'request_changes')">تعديل</button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('❌ Approvals error:', error);
        listDiv.innerHTML = '<div class="ap-empty">❌ تعذر التحميل</div>';
    }
}

window.decideApproval = async (id, decision) => {
    console.log('🎯 قرار:', decision, 'على:', id);
    const note = prompt('ملاحظات (اختياري):') || '';
    
    try {
        const response = await fetch(API + '/review/' + id + '/decide', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({
                decision: decision,
                reviewer_id: localStorage.getItem('aiq_user') || 'founder',
                note: note
            })
        });
        
        if (!response.ok) throw new Error('فشل');
        
        console.log('✅ تم القرار');
        loadApprovals();
        
    } catch (error) {
        console.error('❌ Decision error:', error);
        alert('خطأ في تنفيذ القرار');
    }
};

// ============ AUDIT ============
async function loadAudit() {
    console.log('📋 تحميل السجل');
    const listDiv = document.getElementById('au-list');
    if (!listDiv) return;
    
    listDiv.innerHTML = '<div class="ap-empty">⏳ جارٍ التحميل...</div>';
    
    try {
        const [pending, history] = await Promise.all([
            fetch(API + '/review/pending', { headers: { 'Authorization': 'Bearer ' + token } }).then(r => r.json()),
            fetch(API + '/review/history', { headers: { 'Authorization': 'Bearer ' + token } }).then(r => r.json())
        ]);
        
        const rows = [
            ...pending.map(i => ({ t: 'approval.requested', d: `${i.action} · ${i.risk}`, c: i.created_at })),
            ...history.map(i => ({ t: 'review.' + i.status, d: `${i.action} · ${i.decided_by || ''}`, c: i.decided_at || i.created_at }))
        ];
        
        rows.sort((a, b) => new Date(b.c) - new Date(a.c));
        
        if (rows.length === 0) {
            listDiv.innerHTML = '<div class="ap-empty">📭 السجل فارغ</div>';
            return;
        }
        
        listDiv.innerHTML = rows.map(r => `
            <div class="au-item">
                <span class="et">${r.t}</span>
                <span class="ed">${r.d}</span>
                <span class="ts">${new Date(r.c).toLocaleString('ar')}</span>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('❌ Audit error:', error);
        listDiv.innerHTML = '<div class="ap-empty">❌ تعذر التحميل</div>';
    }
}

// ============ STUDIO ============
async function loadStudio() {
    console.log('🎨 تحميل الاستوديو');
    const gridDiv = document.getElementById('st-grid');
    if (!gridDiv) return;
    
    gridDiv.innerHTML = '<div class="st-empty">⏳ جارٍ التحميل...</div>';
    
    try {
        const response = await fetch(API + '/studio/assets', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        
        if (!response.ok) throw new Error('فشل');
        
        const items = await response.json();
        console.log('🖼️ أصول:', items.length);
        
        if (items.length === 0) {
            gridDiv.innerHTML = '<div class="st-empty">🎨 لا توجد أصول بعد — اضغط «توليد جديد»</div>';
            return;
        }
        
        gridDiv.innerHTML = items.map(a => `
            <div class="st-item" onclick="editAsset('${a.id}')">
                <img src="${API}${a.url}" alt="">
                <div class="st-meta">
                    <h4>${a.prompt}</h4>
                    <p>${a.kind} · ${new Date(a.created_at).toLocaleDateString('ar')}</p>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('❌ Studio error:', error);
        gridDiv.innerHTML = '<div class="st-empty">❌ تعذر التحميل</div>';
    }
}

window.editAsset = (id) => {
    console.log('✏️ تعديل:', id);
    alert('ميزة التعديل قيد التطوير');
};

// ============ BOOT ============
window.addEventListener('load', () => {
    console.log('🚀 تحميل الصفحة');
    const savedToken = localStorage.getItem('aiq_token');
    if (savedToken) {
        token = savedToken;
        console.log('🔑 Token موجود، عرض التطبيق');
        showApp();
    } else {
        console.log('🔑 لا يوجد Token، عرض تسجيل الدخول');
    }
});
