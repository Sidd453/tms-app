/* ============================================================
   TMS Enterprise — Complete API Layer v3 FIXED
   ============================================================ */

const API_BASE = window.location.origin;

async function api(method, endpoint, body = null, isFormData = false) {
    const url  = API_BASE + endpoint;
    const opts = {
        method,
        credentials: 'include',
        headers: isFormData ? {} : { 'Content-Type': 'application/json' },
    };
    if (body) opts.body = isFormData ? body : JSON.stringify(body);
    try {
        const res  = await fetch(url, opts);
        const data = await res.json();
        return data;
    } catch (err) {
        console.error('API error:', endpoint, err);
        return { success: false, error: 'Cannot reach server. Is Flask running?' };
    }
}

/* ── AUTH ─────────────────────────────────────────────────── */
const Auth = {
    login:          (email, password, role) => api('POST', '/api/auth/login',          { email, password, role }),
    me:             ()                       => api('GET',  '/api/auth/me'),
    updateMe:       (data)                   => api('PUT',  '/api/auth/me',             data),
    logout:         ()                       => api('POST', '/api/auth/logout'),
    sendOtp:        (method, value)          => api('POST', '/api/auth/send-otp',       { method, value }),
    verifyOtp:      (otp)                    => api('POST', '/api/auth/verify-otp',     { otp }),
    resetPassword:  (new_password)           => api('POST', '/api/auth/reset-password', { new_password }),
    changePassword: (current_password, new_password) =>
                                               api('PUT',  '/api/auth/change-password', { current_password, new_password }),
};

/* ── EMPLOYEES ────────────────────────────────────────────── */
const Employees = {
    list:   (params = {}) => api('GET',    '/api/employees?' + new URLSearchParams(params)),
    get:    (id)           => api('GET',    `/api/employees/${id}`),
    create: (data)         => api('POST',   '/api/employees', data),
    update: (id, data)     => api('PUT',    `/api/employees/${id}`, data),
    delete: (id)           => api('DELETE', `/api/employees/${id}`),
};

/* ── USERS ──────────────────────────────────────────────────── */
const Users = {
    list:        (params = {}) => api('GET',    '/api/users?' + new URLSearchParams(params)),
    get:         (id)           => api('GET',    `/api/users/${id}`),
    create:      (data)         => api('POST',   '/api/users', data),
    update:      (id, data)     => api('PUT',    `/api/users/${id}`, data),
    delete:      (id)           => api('DELETE', `/api/users/${id}`),
    uploadPhoto: (id, formData) => api('POST',   `/api/users/${id}/photo`, formData, true),
};

/* ── PROJECT MANAGERS ────────────────────────────────────── */
const PMs = {
    list:          ()          => api('GET',    '/api/pms'),
    create:        (data)      => api('POST',   '/api/pms', data),
    update:        (id, data)  => api('PUT',    `/api/pms/${id}`, data),
    delete:        (id)        => api('DELETE', `/api/pms/${id}`),
    resetPassword: (id)        => api('POST',   `/api/pms/${id}/reset-password`),
};

/* ── PROJECTS ─────────────────────────────────────────────── */
const Projects = {
    list:         (params = {}) => api('GET',    '/api/projects?' + new URLSearchParams(params)),
    get:          (id)           => api('GET',    `/api/projects/${id}`),
    create:       (data)         => api('POST',   '/api/projects', data),
    update:       (id, data)     => api('PUT',    `/api/projects/${id}`, data),
    delete:       (id)           => api('DELETE', `/api/projects/${id}`),
    nextCode:     ()             => api('GET',    '/api/projects/next-code'),
    assignPM:     (project_id, pm_id) => api('POST', '/api/projects/assign-pm', { project_id, pm_id }),
    uploadFile:   (id, formData) => api('POST',   `/api/projects/${id}/files`, formData, true),
    deleteFile:   (pid, fid)     => api('DELETE', `/api/projects/${pid}/files/${fid}`),
    assign:       (id, user_id, role) => api('POST', '/api/projects/assign-pm', { project_id: id, pm_id: user_id }),
};

/* ── TASKS ────────────────────────────────────────────────── */
const Tasks = {
    list:             (params = {}) => api('GET',    '/api/tasks?' + new URLSearchParams(params)),
    get:              (id)           => api('GET',    `/api/tasks/${id}`),
    create:           (data)         => api('POST',   '/api/tasks', data),
    update:           (id, data)     => api('PUT',    `/api/tasks/${id}`, data),
    delete:           (id)           => api('DELETE', `/api/tasks/${id}`),
    nextCode:         ()             => api('GET',    '/api/tasks/next-code'),
    bulk:             (data)         => api('POST',   '/api/tasks/bulk', data),
    bulkCreate:       (tasks)        => api('POST',   '/api/tasks/bulk', { tasks }),
    getComments:      (id)           => api('GET',    `/api/tasks/${id}/comments`),
    addComment:       (id, c)        => api('POST',   `/api/tasks/${id}/comments`, { comment: c }),
    getAttachments:   (id)           => Promise.resolve({ success: true, data: [] }),
    uploadAttachment: (id, fd)       => Promise.resolve({ success: true }),
    getHistory:       (id)           => Promise.resolve({ success: true, data: [] }),
};

/* ── TEAM LEADERS ────────────────────────────────────────── */
const TL = {
    list:   ()          => api('GET',    '/api/tl'),
    create: (data)      => api('POST',   '/api/tl', data),
    update: (id, data)  => api('PUT',    `/api/tl/${id}`, data),
    delete: (id)        => api('DELETE', `/api/tl/${id}`),
};

/* ── DEPARTMENTS ──────────────────────────────────────────── */
const Departments = {
    list:   ()          => api('GET',    '/api/departments'),
    create: (data)      => api('POST',   '/api/departments', data),
    update: (id, data)  => api('PUT',    `/api/departments/${id}`, data),
    delete: (id)        => api('DELETE', `/api/departments/${id}`),
};

/* ── ROLES ────────────────────────────────────────────────── */
const Roles = {
    list:   ()          => api('GET',    '/api/roles'),
    create: (data)      => api('POST',   '/api/roles', data),
    update: (id, data)  => api('PUT',    `/api/roles/${id}`, data),
    delete: (id)        => api('DELETE', `/api/roles/${id}`),
};

/* ── SKILLS ───────────────────────────────────────────────── */
const Skills = {
    list: () => api('GET', '/api/skills'),
};

/* ── DASHBOARD ────────────────────────────────────────────── */
const Dashboard = {
    stats: () => api('GET', '/api/dashboard/stats'),
};

/* ── NOTIFICATIONS ────────────────────────────────────────── */
const Notifications = {
    list:     () => api('GET',  '/api/notifications'),
    markRead: () => api('POST', '/api/notifications/mark-read'),
};

/* ── DATE HELPERS ─────────────────────────────────────────── */
function toDisplayDate(str) {
    if (!str) return '—';
    if (str.includes('/')) return str;
    if (str.includes('-')) {
        const [y, m, d] = str.split('-');
        return `${d}/${m}/${y.slice(2)}`;
    }
    return str;
}
function fromDisplayDate(str) {
    if (!str || str === '—') return '';
    if (str.includes('-')) return str;
    const p = str.split('/');
    if (p.length !== 3) return str;
    return `20${p[2]}-${p[1]}-${p[0]}`;
}
function calcPriority(deadlineStr) {
    if (!deadlineStr) return 'Medium';
    const days = Math.ceil((new Date(deadlineStr) - new Date()) / 86400000);
    if (days < 0)   return 'Overdue';
    if (days <= 3)  return 'Critical';
    if (days <= 7)  return 'High';
    if (days <= 30) return 'Medium';
    return 'Low';
}
function autoGenerateCode(prefix, num) {
    return `${prefix}-${String(num).padStart(3, '0')}`;
}

/* ══════════════════════════════════════════════════════════
   TL DASHBOARD — Auto-connect on load
   ══════════════════════════════════════════════════════════ */
if (document.title && document.title.toLowerCase().includes('team lead')) {
    document.addEventListener('DOMContentLoaded', async () => {
        try {
            const me = await Auth.me();
            if (!me.success) { window.location.href = '/'; return; }
            if (me.data.role !== 'tl') { window.location.href = '/'; return; }
            const u = me.data;
            document.querySelectorAll('#tlName, #tlProfileName, .tl-name-display').forEach(el => { if(el) el.textContent = u.name || u.full_name || ''; });
            document.querySelectorAll('#tlRole, .tl-role-display').forEach(el => { if(el) el.textContent = 'Team Leader'; });
            const nameInput   = document.getElementById('tlProfileNameInput');
            const emailInput  = document.getElementById('tlProfileEmail');
            const mobileInput = document.getElementById('tlProfileMobile');
            if (nameInput)   nameInput.value   = u.name || u.full_name || '';
            if (emailInput)  emailInput.value  = u.official_email || '';
            if (mobileInput) mobileInput.value = u.mobile || '';
            const cpForm = document.getElementById('changePassForm') || document.getElementById('tlChangePassForm');
            if (cpForm) {
                cpForm.onsubmit = async function(e) {
                    e.preventDefault();
                    const curr = document.getElementById('cp-current')?.value || document.getElementById('tlCurrPass')?.value;
                    const newp = document.getElementById('cp-new')?.value     || document.getElementById('tlNewPass')?.value;
                    const conf = document.getElementById('cp-confirm')?.value || document.getElementById('tlConfPass')?.value;
                    if (!curr || !newp || !conf) return Swal.fire('Error','All fields required','error');
                    if (newp !== conf) return Swal.fire('Error','Passwords do not match','warning');
                    const res = await Auth.changePassword(curr, newp);
                    if (res.success) Swal.fire('Success','Password updated!','success');
                    else Swal.fire('Error', res.error || 'Failed','error');
                };
            }
        } catch(err) { console.warn('TL init error:', err); }
    });
}

/* ══════════════════════════════════════════════════════════
   DEV DASHBOARD — Auto-connect on load
   ══════════════════════════════════════════════════════════ */
if (document.title && (document.title.toLowerCase().includes('developer') || document.title.toLowerCase().includes('dev'))) {
    document.addEventListener('DOMContentLoaded', async () => {
        try {
            const me = await Auth.me();
            if (!me.success) { window.location.href = '/'; return; }
            if (me.data.role !== 'developer') { window.location.href = '/'; return; }
            const u = me.data;
            document.querySelectorAll('#devName, .dev-name, #devProfileName').forEach(el => { if (el) el.textContent = u.name || u.full_name || ''; });
            const nameInput  = document.getElementById('edit-name')  || document.getElementById('devEditName');
            const emailInput = document.getElementById('edit-email') || document.getElementById('devEditEmail');
            const skillInput = document.getElementById('edit-tech-stack');
            if (nameInput)  nameInput.value  = u.name || '';
            if (emailInput) emailInput.value = u.official_email || '';
            if (skillInput) skillInput.value = u.skills || '';
            const cpForm = document.getElementById('changePassForm');
            if (cpForm) {
                cpForm.onsubmit = async function(e) {
                    e.preventDefault();
                    const curr = document.getElementById('cp-current')?.value;
                    const newp = document.getElementById('cp-new')?.value;
                    const conf = document.getElementById('cp-confirm')?.value;
                    if (!curr || !newp || !conf) return Swal.fire('Error','All fields required','error');
                    if (newp !== conf) return Swal.fire('Warning','Passwords do not match!','warning');
                    const res = await Auth.changePassword(curr, newp);
                    if (res.success) Swal.fire('Success','Password updated!','success').then(()=> cpForm.reset());
                    else Swal.fire('Error', res.error || 'Failed','error');
                };
            }
        } catch(err) { console.warn('Dev init error:', err); }
    });
}