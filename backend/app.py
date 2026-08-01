"""
TMS - COMPLETE SELF-CONTAINED APP - FIXED VERSION
"""
import os, random
from datetime import datetime, timedelta
from flask import Flask, Blueprint, jsonify, send_from_directory, session, request
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from config import Config
from db import mysql, qone, qall, exe


def create_app():
    base_dir     = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.normpath(os.path.join(base_dir, '..', 'Frontend'))

    app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
    app.config.from_object(Config)

    for sub in ['', 'profiles', 'projects', 'tasks']:
        p = os.path.join(app.config['UPLOAD_FOLDER'], sub) if sub else app.config['UPLOAD_FOLDER']
        os.makedirs(p, exist_ok=True)

    mysql.init_app(app)

    _default_origins = [
        'http://127.0.0.1:5000','http://localhost:5000',
        'http://127.0.0.1:5500','http://localhost:5500',
        'http://192.168.1.3:5000','http://192.168.1.10:5000',
    ]
    _env_origins = [o.strip() for o in os.getenv('CORS_ORIGINS', '').split(',') if o.strip()]
    CORS(app, supports_credentials=True, origins=_env_origins or _default_origins)

    @app.before_request
    def keep_session():
        session.permanent = True
        app.permanent_session_lifetime = timedelta(hours=8)

    # Static pages
    @app.route('/')
    def index(): return send_from_directory(frontend_dir, 'index.html')
    @app.route('/super_admin.html')
    def super_admin(): return send_from_directory(frontend_dir, 'super_admin.html')
    @app.route('/pm_dashboard.html')
    @app.route('/project_manager_dashboard.html')
    def pm_dash(): return send_from_directory(frontend_dir, 'project_manager_dashboard.html')
    @app.route('/tl-dashboard.html')
    def tl_dash(): return send_from_directory(frontend_dir, 'tl-dashboard.html')
    @app.route('/dev-dashboard.html')
    @app.route('/developer-dashboard.html')
    def dev_dash(): return send_from_directory(frontend_dir, 'dev-dashboard-pro.html')
    @app.route('/api.js')
    def api_js(): return send_from_directory(frontend_dir, 'api.js')
    @app.route('/static/uploads/<path:filename>')
    def uploads(filename): return send_from_directory(os.path.join(base_dir,'static','uploads'), filename)
    @app.route('/<path:filename>')
    def static_files(filename):
        if filename.startswith('api/'): return jsonify(success=False,error='Not found'),404
        try: return send_from_directory(frontend_dir, filename)
        except: return send_from_directory(frontend_dir, 'index.html')

    # Error handlers
    @app.errorhandler(400)
    def e400(e): return jsonify(success=False,error='Bad request'),400
    @app.errorhandler(401)
    def e401(e): return jsonify(success=False,error='Unauthorized'),401
    @app.errorhandler(404)
    def e404(e): return jsonify(success=False,error='Not found'),404
    @app.errorhandler(405)
    def e405(e): return jsonify(success=False,error='Method not allowed'),405
    @app.errorhandler(500)
    def e500(e): return jsonify(success=False,error='Server error'),500

    _auth(app)
    _employees(app)
    _pm(app)
    _projects(app)
    _tasks(app)
    _departments(app)
    _roles(app)
    _profile(app)
    _tl(app)
    _dashboard(app)

    return app


def _uid(): return session.get('uid') or session.get('user_id')
def _urole(): return session.get('urole','')
def _fdate(d):
    if not d: return ''
    return d.strftime('%d/%m/%y') if hasattr(d,'strftime') else str(d)
ALLOWED_IMG = {'png','jpg','jpeg','gif','webp'}
ALLOWED_DOC = {'pdf','png','jpg','jpeg','gif','webp','doc','docx','xls','xlsx','txt','zip'}


# AUTH
def _auth(app):
    bp = Blueprint('auth', __name__, url_prefix='/api/auth')

    @bp.route('/login', methods=['POST'])
    def login():
        d   = request.get_json(force=True) or {}
        em  = (d.get('email') or '').strip().lower()
        pw  = (d.get('password') or '').strip()
        rol = (d.get('role') or '').strip()
        if not em or not pw or not rol:
            return jsonify(success=False, error='Email, password and role are required'), 400
        user = qone("SELECT * FROM users WHERE LOWER(official_email)=%s AND status='active'", (em,))
        if not user:
            return jsonify(success=False, error='No account found with this email'), 401
        if not check_password_hash(user['password_hash'], pw):
            return jsonify(success=False, error='Wrong password'), 401
        if user['role'] != rol:
            return jsonify(success=False, error=f"Wrong role. Account role is '{user['role']}'. Select correct role card."), 403
        session.permanent = True
        session['uid']     = user['id']
        session['user_id'] = user['id']
        session['urole']   = user['role']
        session['uname']   = user['full_name']
        return jsonify(success=True, data={
            'id':user['id'],'emp_id':user.get('emp_id',''),
            'name':user['full_name'],'role':user['role'],'email':user['official_email']
        })

    @bp.route('/logout', methods=['POST'])
    def logout():
        session.clear(); return jsonify(success=True)

    @bp.route('/me', methods=['GET'])
    def me():
        uid = _uid()
        if not uid: return jsonify(success=False,error='Not logged in'),401
        user = qone("SELECT * FROM users WHERE id=%s",(uid,))
        if not user: return jsonify(success=False,error='User not found'),404
        loc=''; pic=user.get('profile_pic') or ''
        if user['role']=='superadmin':
            ap=qone("SELECT * FROM admin_profile WHERE id=1")
            if ap: loc=ap.get('location') or ''; pic=pic or ap.get('profile_pic') or ''
        return jsonify(success=True, data={
            'id':user['id'],'emp_id':user.get('emp_id',''),
            'name':user['full_name'],'full_name':user['full_name'],
            'role':user['role'],'official_email':user['official_email'],
            'personal_email':user.get('personal_email') or '',
            'mobile':user.get('mobile') or '','location':loc,'profile_pic':pic
        })

    @bp.route('/me', methods=['PUT'])
    def update_me():
        uid=_uid()
        if not uid: return jsonify(success=False,error='Unauthorized'),401
        d=request.get_json(force=True) or {}
        name=(d.get('full_name') or '').strip()
        if not name: return jsonify(success=False,error='Name required'),400
        em=d.get('official_email') or ''; mob=d.get('mobile') or ''; loc=d.get('location') or ''
        exe("UPDATE users SET full_name=%s,official_email=%s,mobile=%s WHERE id=%s",(name,em,mob,uid))
        if session.get('urole')=='superadmin':
            if qone("SELECT id FROM admin_profile WHERE id=1"):
                exe("UPDATE admin_profile SET full_name=%s,official_email=%s,mobile=%s,location=%s WHERE id=1",(name,em,mob,loc))
            else:
                exe("INSERT INTO admin_profile(id,full_name,official_email,mobile,location) VALUES(1,%s,%s,%s,%s)",(name,em,mob,loc))
        session['uname']=name
        return jsonify(success=True)

    @bp.route('/change-password', methods=['PUT'])
    def change_pw():
        uid=_uid()
        if not uid: return jsonify(success=False,error='Unauthorized'),401
        d=request.get_json(force=True) or {}
        curr=d.get('current_password') or ''; newp=d.get('new_password') or ''
        if not curr or not newp or len(newp)<6: return jsonify(success=False,error='Both passwords required'),400
        user=qone("SELECT password_hash FROM users WHERE id=%s",(uid,))
        if not user or not check_password_hash(user['password_hash'],curr): return jsonify(success=False,error='Current password incorrect'),403
        exe("UPDATE users SET password_hash=%s WHERE id=%s",(generate_password_hash(newp),uid))
        return jsonify(success=True)

    @bp.route('/send-otp', methods=['POST'])
    def send_otp():
        d=request.get_json(force=True) or {}
        method=d.get('method','email'); value=(d.get('value') or '').strip()
        if not value: return jsonify(success=False,error='Contact required'),400
        found=qone("SELECT id FROM users WHERE LOWER(official_email)=LOWER(%s)",(value,)) if method=='email' else qone("SELECT id FROM users WHERE mobile=%s",(value,))
        if not found: return jsonify(success=False,error='No account found'),404
        otp=str(random.randint(100000,999999)); exp=datetime.utcnow()+timedelta(minutes=10)
        exe("UPDATE otp_tokens SET is_used=1 WHERE contact_value=%s AND is_used=0",(value,))
        exe("INSERT INTO otp_tokens(contact_value,contact_type,otp_code,purpose,expires_at) VALUES(%s,%s,%s,'forgot_password',%s)",(value,method,otp,exp))
        session['otp_contact']=value; session['otp_verified']=False
        return jsonify(success=True,otp=otp)

    @bp.route('/verify-otp', methods=['POST'])
    def verify_otp():
        d=request.get_json(force=True) or {}
        otp=(d.get('otp') or '').strip(); contact=session.get('otp_contact')
        if not otp or not contact: return jsonify(success=False,error='OTP required'),400
        tok=qone("SELECT id FROM otp_tokens WHERE contact_value=%s AND otp_code=%s AND is_used=0 AND expires_at>UTC_TIMESTAMP() ORDER BY id DESC LIMIT 1",(contact,otp))
        if not tok: return jsonify(success=False,error='Invalid or expired OTP'),400
        exe("UPDATE otp_tokens SET is_used=1 WHERE id=%s",(tok['id'],))
        session['otp_verified']=True; return jsonify(success=True)

    @bp.route('/reset-password', methods=['POST'])
    def reset_pw():
        if not session.get('otp_verified'): return jsonify(success=False,error='OTP verification required'),403
        d=request.get_json(force=True) or {}; pw=d.get('new_password') or ''
        if len(pw)<6: return jsonify(success=False,error='Password too short'),400
        contact=session.get('otp_contact','')
        exe("UPDATE users SET password_hash=%s WHERE LOWER(official_email)=LOWER(%s)",(generate_password_hash(pw),contact))
        session.pop('otp_contact',None); session.pop('otp_verified',None)
        return jsonify(success=True)

    app.register_blueprint(bp)


# EMPLOYEES + USERS
def _employees(app):
    bp = Blueprint('employees', __name__)

    def _se(u):
        return {
            'id':u['id'],'emp_id':u.get('emp_id') or '',
            'name':u['full_name'],'full_name':u['full_name'],
            'officialEmail':u.get('official_email') or '',
            'personalEmail':u.get('personal_email') or '',
            'mobile':u.get('mobile') or '',
            'dept':u.get('department') or '',
            'department':u.get('department') or '',
            'role':u.get('designation') or u.get('role') or '',
            'doj':_fdate(u.get('doj')),
            'location':u.get('work_location') or '',
            'skills':u.get('skills') or '',
            'profile_pic':u.get('profile_pic') or '',
            'status':u.get('status') or 'active'
        }

    def _sp(p):
        return {
            'id':p['id'],'emp_id':p.get('emp_id') or '','empId':p.get('emp_id') or '',
            'name':p['full_name'],'email':p.get('official_email') or '',
            'officialEmail':p.get('official_email') or '',
            'personalEmail':p.get('personal_email') or '',
            'mobile':p.get('mobile') or '',
            'exp':str(p.get('experience_yrs') or 0),
            'domain':p.get('primary_domain') or '',
            'client':p.get('initial_client') or '',
            'status':p.get('status') or 'active'
        }

    @bp.route('/api/employees', methods=['GET'])
    @bp.route('/api/users', methods=['GET'])
    def list_users():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        rid=request.args.get('role_id'); q=request.args.get('q','')
        role_filter=request.args.get('role','')
        if rid=='2':
            return jsonify(success=True,data=[_sp(r) for r in qall("SELECT * FROM project_managers ORDER BY created_at DESC")])
        if q:
            s=f'%{q}%'
            rows=qall("SELECT * FROM users WHERE role!='superadmin' AND (full_name LIKE %s OR official_email LIKE %s OR emp_id LIKE %s) ORDER BY created_at DESC",(s,s,s))
        elif role_filter:
            rows=qall("SELECT * FROM users WHERE role=%s ORDER BY created_at DESC",(role_filter,))
        else:
            rows=qall("SELECT * FROM users WHERE role!='superadmin' ORDER BY created_at DESC")
        return jsonify(success=True,data=[_se(r) for r in rows])

    @bp.route('/api/employees', methods=['POST'])
    @bp.route('/api/users', methods=['POST'])
    def create_user():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        d=request.get_json(force=True) or {}
        name=(d.get('full_name') or '').strip()
        email=(d.get('official_email') or d.get('email') or '').strip().lower()
        if not name or not email: return jsonify(success=False,error='Name and email required'),400

        # ── PM creation path ──
        if 'experience_yrs' in d or 'primary_domain' in d:
            if qone("SELECT id FROM project_managers WHERE official_email=%s",(email,)):
                return jsonify(success=False,error='PM email already exists'),409
            try:
                count=(qone("SELECT COUNT(*) AS c FROM project_managers") or {}).get('c',0)
                eid=f"EMP-PM-{count+1:03d}"
                # ensure unique emp_id
                while qone("SELECT id FROM project_managers WHERE emp_id=%s",(eid,)):
                    count+=1; eid=f"EMP-PM-{count+1:03d}"
                pw=f"{eid}@TMS"
                pid=exe("INSERT INTO project_managers(emp_id,full_name,official_email,personal_email,mobile,password_hash,experience_yrs,primary_domain,initial_client) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (eid,name,email,d.get('personal_email') or None,d.get('mobile') or None,
                     generate_password_hash(pw),int(d.get('experience_yrs') or 0),
                     d.get('primary_domain') or None,d.get('initial_client') or None))
                if not qone("SELECT id FROM users WHERE official_email=%s",(email,)):
                    exe("INSERT INTO users(emp_id,full_name,official_email,mobile,password_hash,role,status) VALUES(%s,%s,%s,%s,%s,'pm','active')",
                        (eid,name,email,d.get('mobile') or None,generate_password_hash(pw)))
                pm=qone("SELECT * FROM project_managers WHERE id=%s",(pid,))
                return jsonify(success=True,data={**_sp(pm),'temp_password':pw}),201
            except Exception as e:
                print(f"[create PM error] {e}")
                return jsonify(success=False,error=f'Could not create PM: {str(e)}'),500

        # ── Regular employee creation path ──
        if qone("SELECT id FROM users WHERE official_email=%s",(email,)):
            return jsonify(success=False,error='Email already exists. Use a different email.'),409

        RMAP={
            'juniordeveloper':'developer','seniordeveloper':'developer',
            'developer':'developer','teamleader':'tl','tl':'tl',
            'projectmanager':'pm','pm':'pm',
            'uiuxdesigner':'developer','qaengineer':'developer','hrexecutive':'developer'
        }
        role_raw=(d.get('role') or 'developer').strip()
        rc=RMAP.get(role_raw.lower().replace(' ','').replace('/',''),'developer')

        # FIX: clean up "Select Dept" default value
        dept_raw=d.get('department') or ''
        dept = None if dept_raw in ('', 'Select Dept', 'Select Department') else dept_raw

        # FIX: generate truly unique emp_id
        try:
            count=(qone("SELECT COUNT(*) AS c FROM users WHERE role!='superadmin'") or {}).get('c',0)
            eid=f"EMP-{count+1:03d}"
            while qone("SELECT id FROM users WHERE emp_id=%s",(eid,)):
                count+=1; eid=f"EMP-{count+1:03d}"
            pw=f"TMS@{eid}"
            uid=exe(
                "INSERT INTO users(emp_id,full_name,official_email,personal_email,mobile,"
                "password_hash,role,department,designation,doj,work_location,skills,status) "
                "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'active')",
                (eid, name, email,
                 d.get('personal_email') or None,
                 d.get('mobile') or None,
                 generate_password_hash(pw),
                 rc, dept,
                 role_raw,                          # store display name as designation
                 d.get('doj') or None,
                 d.get('work_location') or None,
                 d.get('skills') or None))
            row=qone("SELECT * FROM users WHERE id=%s",(uid,))
            return jsonify(success=True, data=_se(row), temp_password=pw), 201
        except Exception as e:
            print(f"[create_user error] {e}")
            return jsonify(success=False, error=f'Could not add employee: {str(e)}'), 500

    @bp.route('/api/employees/<int:eid>', methods=['PUT'])
    @bp.route('/api/users/<int:eid>', methods=['PUT'])
    def update_user(eid):
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        d=request.get_json(force=True) or {}
        try:
            if 'experience_yrs' in d or 'primary_domain' in d:
                exe("UPDATE project_managers SET full_name=%s,official_email=%s,personal_email=%s,mobile=%s,experience_yrs=%s,primary_domain=%s WHERE id=%s",
                    (d.get('full_name'),d.get('official_email'),d.get('personal_email') or None,
                     d.get('mobile') or None,int(d.get('experience_yrs') or 0),d.get('primary_domain') or None,eid))
                pm=qone("SELECT * FROM project_managers WHERE id=%s",(eid,))
                return jsonify(success=True,data=_sp(pm) if pm else {})
            dept_raw=d.get('department') or ''
            dept=None if dept_raw in ('','Select Dept','Select Department') else dept_raw
            role_raw=(d.get('role') or d.get('designation') or '').strip()
            exe("UPDATE users SET full_name=%s,official_email=%s,personal_email=%s,mobile=%s,department=%s,designation=%s,doj=%s,work_location=%s,skills=%s WHERE id=%s",
                (d.get('full_name'),d.get('official_email') or d.get('email'),
                 d.get('personal_email') or None,d.get('mobile') or None,
                 dept, role_raw or None,
                 d.get('doj') or None,d.get('work_location') or None,d.get('skills') or None,eid))
            row=qone("SELECT * FROM users WHERE id=%s",(eid,))
            return jsonify(success=True,data=_se(row) if row else {})
        except Exception as e:
            print(f"[update_user error] {e}")
            return jsonify(success=False,error=f'Update failed: {str(e)}'),500

    @bp.route('/api/employees/<int:eid>', methods=['DELETE'])
    @bp.route('/api/users/<int:eid>', methods=['DELETE'])
    def delete_user(eid):
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        try:
            exe("DELETE FROM users WHERE id=%s AND role!='superadmin'",(eid,))
            return jsonify(success=True)
        except Exception as e:
            return jsonify(success=False,error=str(e)),500

    @bp.route('/api/users/<int:uid>/photo', methods=['POST'])
    def upload_photo(uid):
        from flask import current_app
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        file=request.files.get('photo')
        if not file or not file.filename: return jsonify(success=False,error='No file'),400
        ext=file.filename.rsplit('.',1)[-1].lower() if '.' in file.filename else ''
        if ext not in ALLOWED_IMG: return jsonify(success=False,error='Invalid type'),400
        folder=os.path.join(current_app.config['UPLOAD_FOLDER'],'profiles')
        os.makedirs(folder,exist_ok=True)
        fn=secure_filename(f"user_{uid}.{ext}"); file.save(os.path.join(folder,fn))
        url=f"/static/uploads/profiles/{fn}"
        exe("UPDATE users SET profile_pic=%s WHERE id=%s",(url,uid))
        if session.get('urole')=='superadmin':
            exe("UPDATE admin_profile SET profile_pic=%s WHERE id=1",(url,))
        return jsonify(success=True,data={'photo_url':url})

    app.register_blueprint(bp)


# PROJECT MANAGERS
def _pm(app):
    bp=Blueprint('pm',__name__,url_prefix='/api/pms')
    def _s(p): return {
        'id':p['id'],'empId':p.get('emp_id') or '','emp_id':p.get('emp_id') or '',
        'name':p['full_name'],'email':p.get('official_email') or '',
        'personalEmail':p.get('personal_email') or '','mobile':p.get('mobile') or '',
        'exp':str(p.get('experience_yrs') or 0),'domain':p.get('primary_domain') or '',
        'client':p.get('initial_client') or '','status':p.get('status') or 'active'
    }

    @bp.route('',methods=['GET'])
    def list_pms():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        return jsonify(success=True,data=[_s(r) for r in qall("SELECT * FROM project_managers ORDER BY id DESC")])

    @bp.route('',methods=['POST'])
    def create_pm():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        d=request.get_json(force=True) or {}
        name=(d.get('full_name') or '').strip(); email=(d.get('official_email') or '').strip().lower()
        if not name or not email: return jsonify(success=False,error='Name and email required'),400
        if qone("SELECT id FROM project_managers WHERE official_email=%s",(email,)):
            return jsonify(success=False,error='Email exists'),409
        count=(qone("SELECT COUNT(*) AS c FROM project_managers") or {}).get('c',0)
        eid=f"EMP-PM-{count+1:03d}"; pw=f"{eid}@TMS"
        pid=exe("INSERT INTO project_managers(emp_id,full_name,official_email,personal_email,mobile,password_hash,experience_yrs,primary_domain,initial_client,status) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,'active')",
            (eid,name,email,d.get('personal_email') or None,d.get('mobile') or None,
             generate_password_hash(pw),int(d.get('experience_yrs') or 0),
             d.get('primary_domain') or None,d.get('initial_client') or None))
        if not qone("SELECT id FROM users WHERE official_email=%s",(email,)):
            exe("INSERT INTO users(emp_id,full_name,official_email,mobile,password_hash,role,status) VALUES(%s,%s,%s,%s,%s,'pm','active')",
                (eid,name,email,d.get('mobile') or None,generate_password_hash(pw)))
        pm=qone("SELECT * FROM project_managers WHERE id=%s",(pid,))
        return jsonify(success=True,data={**_s(pm),'temp_password':pw,'empId':eid}),201

    @bp.route('/<int:pid>',methods=['PUT'])
    def update_pm(pid):
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        d=request.get_json(force=True) or {}
        exe("UPDATE project_managers SET full_name=%s,official_email=%s,personal_email=%s,mobile=%s,experience_yrs=%s,primary_domain=%s WHERE id=%s",
            (d.get('full_name'),d.get('official_email'),d.get('personal_email') or None,
             d.get('mobile') or None,int(d.get('experience_yrs') or 0),d.get('primary_domain') or None,pid))
        pm=qone("SELECT * FROM project_managers WHERE id=%s",(pid,))
        return jsonify(success=True,data=_s(pm) if pm else {})

    @bp.route('/<int:pid>',methods=['DELETE'])
    def delete_pm(pid):
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        pm=qone("SELECT official_email FROM project_managers WHERE id=%s",(pid,))
        exe("UPDATE projects SET assigned_pm_id=NULL WHERE assigned_pm_id=%s",(pid,))
        exe("DELETE FROM project_managers WHERE id=%s",(pid,))
        if pm: exe("DELETE FROM users WHERE official_email=%s AND role='pm'",(pm['official_email'],))
        return jsonify(success=True)

    @bp.route('/<int:pid>/reset-password',methods=['POST'])
    def reset_pw(pid):
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        pm=qone("SELECT * FROM project_managers WHERE id=%s",(pid,))
        if not pm: return jsonify(success=False,error='Not found'),404
        pw=f"{pm['emp_id']}@TMS"; h=generate_password_hash(pw)
        exe("UPDATE project_managers SET password_hash=%s WHERE id=%s",(h,pid))
        exe("UPDATE users SET password_hash=%s WHERE official_email=%s",(h,pm['official_email']))
        return jsonify(success=True,data={'email':pm['official_email'],'default_password':pw})

    app.register_blueprint(bp)


# PROJECTS
def _projects(app):
    from flask import current_app
    bp=Blueprint('projects',__name__,url_prefix='/api/projects')

    def _s(p):
        files=qall("SELECT id,file_label,file_path FROM project_files WHERE project_id=%s",(p['id'],))
        pmn=''
        if p.get('assigned_pm_id'):
            r=qone("SELECT full_name FROM project_managers WHERE id=%s",(p['assigned_pm_id'],))
            if r: pmn=r['full_name']
        return {
            'id':p['id'],'code':p['project_code'],'name':p['project_name'],
            'client':p.get('client_name') or '','assigned':_fdate(p.get('date_assigned')),
            'deadline':_fdate(p.get('target_deadline')),'hours':p.get('estimated_hours') or '',
            'status':p.get('status') or 'Planned','priority':p.get('priority') or 'Low',
            'desc':p.get('description') or '','progress':p.get('progress') or 0,
            'assigned_pm':pmn,'assigned_pm_id':p.get('assigned_pm_id'),
            'files':[f['file_label'] for f in files],
            'files_full':[{'id':f['id'],'label':f['file_label'],'path':f.get('file_path') or ''} for f in files]
        }

    @bp.route('/next-code',methods=['GET'])
    def next_code():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        c=(qone("SELECT COUNT(*) AS c FROM projects") or {}).get('c',0)
        return jsonify(success=True,code=f"PRJ-{c+1:03d}",data={'next_num':c+1})

    @bp.route('',methods=['GET'])
    def list_p():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        role = session.get('urole','')
        if role == 'pm':
            pm = qone('SELECT id FROM project_managers WHERE official_email=(SELECT official_email FROM users WHERE id=%s)',(_uid(),))
            rows = qall('SELECT * FROM projects WHERE assigned_pm_id=%s ORDER BY id DESC',(pm['id'],)) if pm else []
        else:
            rows = qall('SELECT * FROM projects ORDER BY id DESC')
        return jsonify(success=True,data=[_s(p) for p in rows])


    @bp.route('',methods=['POST'])
    def create_p():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        d=request.get_json(force=True) or {}
        name=(d.get('project_name') or '').strip()
        if not name: return jsonify(success=False,error='Project name required'),400
        try:
            code=(d.get('project_code') or '').strip()
            if not code:
                c=(qone("SELECT COUNT(*) AS c FROM projects") or {}).get('c',0)
                abbr=name.replace(' ','').upper()[:3]
                cli=(d.get('client_name') or 'GEN').replace(' ','').upper()[:3]
                code=f"PRJ-{abbr}-{cli}-{c+1:03d}"
                # ensure unique
                while qone("SELECT id FROM projects WHERE project_code=%s",(code,)):
                    c+=1; code=f"PRJ-{abbr}-{cli}-{c+1:03d}"
            pid=exe("INSERT INTO projects(project_code,project_name,client_name,date_assigned,target_deadline,estimated_hours,priority,status,description,progress,created_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,0,%s)",
                (code,name,d.get('client_name') or None,d.get('date_assigned') or None,
                 d.get('target_deadline') or None,d.get('estimated_hours') or None,
                 d.get('priority') or 'Low',d.get('status') or 'Planned',
                 d.get('description') or None,_uid()))
            for lbl in (d.get('files') or []):
                if lbl: exe("INSERT INTO project_files(project_id,file_label) VALUES(%s,%s)",(pid,lbl))
            p=qone("SELECT * FROM projects WHERE id=%s",(pid,))
            return jsonify(success=True,data=_s(p)),201
        except Exception as e:
            print(f"[create_p error] {e}")
            return jsonify(success=False,error=f'Could not create project: {str(e)}'),500

    @bp.route('/<int:pid>',methods=['GET'])
    def get_p(pid):
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        p=qone("SELECT * FROM projects WHERE id=%s",(pid,))
        return jsonify(success=True,data=_s(p)) if p else (jsonify(success=False,error='Not found'),404)

    @bp.route('/<int:pid>',methods=['PUT'])
    def update_p(pid):
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        d=request.get_json(force=True) or {}
        exe("UPDATE projects SET project_name=%s,client_name=%s,date_assigned=%s,target_deadline=%s,estimated_hours=%s,priority=%s,status=%s,description=%s,progress=%s WHERE id=%s",
            (d.get('project_name'),d.get('client_name'),d.get('date_assigned') or None,
             d.get('target_deadline') or None,d.get('estimated_hours'),d.get('priority'),
             d.get('status'),d.get('description'),d.get('progress',0),pid))
        p=qone("SELECT * FROM projects WHERE id=%s",(pid,))
        return jsonify(success=True,data=_s(p))

    @bp.route('/<int:pid>',methods=['DELETE'])
    def delete_p(pid):
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        exe("DELETE FROM projects WHERE id=%s",(pid,))
        return jsonify(success=True)

    @bp.route('/assign-pm',methods=['POST'])
    def assign_pm():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        d=request.get_json(force=True) or {}
        pid=d.get('project_id'); pmid=d.get('pm_id')
        if not pid or not pmid: return jsonify(success=False,error='project_id and pm_id required'),400
        exe("UPDATE projects SET assigned_pm_id=%s,status='Active' WHERE id=%s",(pmid,pid))
        return jsonify(success=True)

    @bp.route('/<int:pid>/files',methods=['POST'])
    def upload_file(pid):
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        label=request.form.get('label','').strip(); file=request.files.get('file'); path=None
        if file and file.filename:
            ext=file.filename.rsplit('.',1)[-1].lower() if '.' in file.filename else ''
            if ext in ALLOWED_DOC:
                folder=os.path.join(current_app.config['UPLOAD_FOLDER'],'projects',str(pid))
                os.makedirs(folder,exist_ok=True); fn=secure_filename(file.filename)
                file.save(os.path.join(folder,fn)); path=f"/static/uploads/projects/{pid}/{fn}"
        if not label and file: label=file.filename or 'file'
        if not label: return jsonify(success=False,error='Label required'),400
        fid=exe("INSERT INTO project_files(project_id,file_label,file_path) VALUES(%s,%s,%s)",(pid,label,path))
        return jsonify(success=True,data={'id':fid,'label':label,'path':path}),201

    @bp.route('/<int:pid>/files/<int:fid>',methods=['DELETE'])
    def delete_file(pid,fid):
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        exe("DELETE FROM project_files WHERE id=%s AND project_id=%s",(fid,pid))
        return jsonify(success=True)

    app.register_blueprint(bp)


# TASKS
def _tasks(app):
    bp=Blueprint('tasks',__name__,url_prefix='/api/tasks')

    def _auto_pri(dl):
        if not dl: return 'Medium'
        from datetime import date
        try:
            d=datetime.strptime(dl,'%Y-%m-%d').date() if isinstance(dl,str) else dl
            days=(d-date.today()).days
            if days<0: return 'Overdue'
            if days<=3: return 'Critical'
            if days<=7: return 'High'
            if days<=30: return 'Medium'
            return 'Low'
        except: return 'Medium'

    def _next_code():
        n=(qone("SELECT COALESCE(MAX(id),0)+1 AS n FROM tasks") or {}).get('n',1)
        code=f"TK-{n:03d}"
        while qone("SELECT id FROM tasks WHERE task_code=%s",(code,)): n+=1; code=f"TK-{n:03d}"
        return code

    def _s(t):
        proj=qone("SELECT project_code,project_name FROM projects WHERE id=%s",(t['project_id'],)) if t.get('project_id') else None
        return {
            'id':t['id'],'code':t.get('task_code') or '',
            'name':t.get('task_name') or '','task_name':t.get('task_name') or '',
            'project_id':t.get('project_id'),
            'project_code':proj['project_code'] if proj else '',
            'project_name':proj['project_name'] if proj else '',
            'assigned_tl':t.get('assigned_tl') or '',
            'assigned_dev':t.get('assigned_dev') or '',
            'deadline':_fdate(t.get('deadline')),
            'date_assigned':_fdate(t.get('date_assigned')),
            'hours':t.get('estimated_hours') or '',
            'expertise':t.get('expertise_level') or '',
            'department':t.get('department') or '',
            'skills':t.get('required_skills') or '',
            'required_skills':t.get('required_skills') or '',
            'remark':t.get('remark') or '',
            'priority':t.get('priority') or 'Medium',
            'status':t.get('status') or 'Pending',
            'progress':t.get('progress') or 0
        }

    @bp.route('/next-code',methods=['GET'])
    def next_code():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        code=_next_code(); num=int(code.split('-')[1])
        return jsonify(success=True,data={'next_num':num,'code':code})

    @bp.route('',methods=['GET'])
    def list_t():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        role = _urole()
        uid  = _uid()
        pid  = request.args.get('project_id')

        # Role-based filtering
        if role == 'developer':
            # Developer sirf apni assigned tasks dekhega
            user = qone("SELECT full_name FROM users WHERE id=%s", (uid,))
            uname = user['full_name'] if user else ''
            if pid:
                rows = qall("SELECT * FROM tasks WHERE project_id=%s AND assigned_dev=%s ORDER BY id DESC", (pid, uname))
            else:
                rows = qall("SELECT * FROM tasks WHERE assigned_dev=%s ORDER BY id DESC", (uname,))
        elif role == 'tl':
            # TL sirf apni assigned tasks dekhega
            user = qone("SELECT full_name FROM users WHERE id=%s", (uid,))
            uname = user['full_name'] if user else ''
            if pid:
                rows = qall("SELECT * FROM tasks WHERE project_id=%s AND assigned_tl=%s ORDER BY id DESC", (pid, uname))
            else:
                rows = qall("SELECT * FROM tasks WHERE assigned_tl=%s ORDER BY id DESC", (uname,))
        elif role == 'pm':
            # PM sirf apne projects ki tasks dekhega
            pm = qone('SELECT id FROM project_managers WHERE official_email=(SELECT official_email FROM users WHERE id=%s)', (uid,))
            if pm:
                if pid:
                    rows = qall("SELECT t.* FROM tasks t JOIN projects p ON t.project_id=p.id WHERE p.assigned_pm_id=%s AND t.project_id=%s ORDER BY t.id DESC", (pm['id'], pid))
                else:
                    rows = qall("SELECT t.* FROM tasks t JOIN projects p ON t.project_id=p.id WHERE p.assigned_pm_id=%s ORDER BY t.id DESC", (pm['id'],))
            else:
                rows = []
        else:
            # Superadmin - sab tasks
            rows = qall("SELECT * FROM tasks WHERE project_id=%s ORDER BY id DESC", (pid,)) if pid else qall("SELECT * FROM tasks ORDER BY id DESC")

        return jsonify(success=True, data=[_s(r) for r in rows])

    @bp.route('',methods=['POST'])
    def create_t():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        d=request.get_json(force=True) or {}
        name=(d.get('task_name') or d.get('name') or '').strip()
        if not name: return jsonify(success=False,error='Task name required'),400
        code=d.get('task_code') or _next_code()
        pri=d.get('priority') or _auto_pri(d.get('deadline'))
        tid=exe("INSERT INTO tasks(task_code,task_name,project_id,assigned_pm_id,assigned_tl,assigned_dev,date_assigned,deadline,estimated_hours,expertise_level,department,required_skills,remark,priority,status,progress) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0)",
            (code,name,d.get('project_id') or None,_uid(),
             d.get('assigned_tl') or None,d.get('assigned_dev') or None,
             d.get('date_assigned') or None,d.get('deadline') or None,
             d.get('estimated_hours') or None,d.get('expertise_level') or None,
             d.get('department') or None,d.get('required_skills') or None,
             d.get('remark') or None,pri,d.get('status') or 'Pending'))
        t=qone("SELECT * FROM tasks WHERE id=%s",(tid,))
        return jsonify(success=True,data=_s(t)),201

    @bp.route('/bulk',methods=['POST'])
    def bulk_t():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        items=(request.get_json(force=True) or {}).get('tasks') or []
        if not items: return jsonify(success=False,error='No tasks'),400
        created=[]
        for item in items:
            name=(item.get('task_name') or item.get('name') or '').strip()
            if not name: continue
            code=item.get('task_code') or _next_code()
            pri=item.get('priority') or _auto_pri(item.get('deadline'))
            tid=exe("INSERT INTO tasks(task_code,task_name,project_id,assigned_pm_id,assigned_tl,assigned_dev,date_assigned,deadline,estimated_hours,expertise_level,department,required_skills,remark,priority,status,progress) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0)",
                (code,name,item.get('project_id') or None,_uid(),
                 item.get('assigned_tl') or None,item.get('assigned_dev') or None,
                 item.get('date_assigned') or None,item.get('deadline') or None,
                 item.get('estimated_hours') or None,item.get('expertise_level') or None,
                 item.get('department') or None,item.get('required_skills') or None,
                 item.get('remark') or None,pri,item.get('status') or 'Pending'))
            t=qone("SELECT * FROM tasks WHERE id=%s",(tid,))
            if t: created.append(_s(t))
        return jsonify(success=True,data=created,count=len(created)),201

    @bp.route('/<int:tid>',methods=['GET'])
    def get_t(tid):
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        t=qone("SELECT * FROM tasks WHERE id=%s",(tid,))
        return jsonify(success=True,data=_s(t)) if t else (jsonify(success=False,error='Not found'),404)

    @bp.route('/<int:tid>',methods=['PUT'])
    def update_t(tid):
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        d=request.get_json(force=True) or {}
        pri=d.get('priority') or _auto_pri(d.get('deadline'))
        exe("UPDATE tasks SET task_name=%s,assigned_tl=%s,assigned_dev=%s,deadline=%s,priority=%s,status=%s,progress=%s,remark=%s WHERE id=%s",
            (d.get('task_name'),d.get('assigned_tl') or None,d.get('assigned_dev') or None,
             d.get('deadline') or None,pri,d.get('status') or 'Pending',
             d.get('progress',0),d.get('remark') or None,tid))
        t=qone("SELECT * FROM tasks WHERE id=%s",(tid,))
        return jsonify(success=True,data=_s(t))

    @bp.route('/<int:tid>',methods=['DELETE'])
    def delete_t(tid):
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        exe("DELETE FROM tasks WHERE id=%s",(tid,))
        return jsonify(success=True)

    @bp.route('/<int:tid>/comments',methods=['GET'])
    def get_comments(tid):
        return jsonify(success=True,data=[])
    @bp.route('/<int:tid>/comments',methods=['POST'])
    def add_comment(tid):
        return jsonify(success=True,data={'id':0})

    app.register_blueprint(bp)


# DEPARTMENTS
def _departments(app):
    bp=Blueprint('departments',__name__,url_prefix='/api/departments')
    def _s(d): return {
        'id':d['id'],'name':d.get('dept_name') or '','dept_name':d.get('dept_name') or '',
        'hod':d.get('hod_name') or '','hod_name':d.get('hod_name') or '',
        'members':d.get('member_count') or 0,'member_count':d.get('member_count') or 0,
        'description':d.get('description') or ''
    }

    @bp.route('',methods=['GET'])
    def list_d():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        return jsonify(success=True,data=[_s(r) for r in qall("SELECT * FROM departments ORDER BY id")])

    @bp.route('',methods=['POST'])
    def create_d():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        d=request.get_json(force=True) or {}
        name=(d.get('dept_name') or '').strip()
        if not name: return jsonify(success=False,error='Name required'),400
        did=exe("INSERT INTO departments(dept_name,hod_name,description,member_count) VALUES(%s,%s,%s,0)",
            (name,d.get('hod_name') or None,d.get('description') or None))
        return jsonify(success=True,data=_s(qone("SELECT * FROM departments WHERE id=%s",(did,)))),201

    @bp.route('/<int:did>',methods=['PUT'])
    def update_d(did):
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        d=request.get_json(force=True) or {}
        exe("UPDATE departments SET dept_name=%s,hod_name=%s,description=%s WHERE id=%s",
            (d.get('dept_name') or '',d.get('hod_name') or None,d.get('description') or None,did))
        return jsonify(success=True,data=_s(qone("SELECT * FROM departments WHERE id=%s",(did,))))

    @bp.route('/<int:did>',methods=['DELETE'])
    def delete_d(did):
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        exe("DELETE FROM departments WHERE id=%s",(did,))
        return jsonify(success=True)

    app.register_blueprint(bp)


# ROLES
def _roles(app):
    bp=Blueprint('roles',__name__,url_prefix='/api/roles')
    def _s(r): return {
        'id':r['id'],'role_name':r.get('role_name') or '',
        'access_level':r.get('access_level') or 'Read Only',
        'description':r.get('description') or ''
    }

    @bp.route('',methods=['GET'])
    def list_r():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        return jsonify(success=True,data=[_s(r) for r in qall("SELECT * FROM roles_custom ORDER BY id")])

    @bp.route('',methods=['POST'])
    def create_r():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        d=request.get_json(force=True) or {}
        name=(d.get('role_name') or '').strip()
        if not name: return jsonify(success=False,error='Name required'),400
        rid=exe("INSERT INTO roles_custom(role_name,access_level,description) VALUES(%s,%s,%s)",
            (name,d.get('access_level') or 'Read Only',d.get('description') or None))
        return jsonify(success=True,data=_s(qone("SELECT * FROM roles_custom WHERE id=%s",(rid,)))),201

    @bp.route('/<int:rid>',methods=['PUT'])
    def update_r(rid):
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        d=request.get_json(force=True) or {}
        exe("UPDATE roles_custom SET role_name=%s,access_level=%s WHERE id=%s",
            (d.get('role_name') or '',d.get('access_level') or 'Read Only',rid))
        return jsonify(success=True,data=_s(qone("SELECT * FROM roles_custom WHERE id=%s",(rid,))))

    @bp.route('/<int:rid>',methods=['DELETE'])
    def delete_r(rid):
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        exe("DELETE FROM roles_custom WHERE id=%s",(rid,))
        return jsonify(success=True)

    app.register_blueprint(bp)


# PROFILE
def _profile(app):
    from flask import current_app
    bp=Blueprint('profile',__name__,url_prefix='/api/profile')

    @bp.route('',methods=['GET'])
    def get_p():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        p=qone("SELECT * FROM admin_profile WHERE id=1")
        if not p: return jsonify(success=True,data={'name':session.get('uname','Admin'),'full_name':session.get('uname','Admin'),'email':'','official_email':'','mobile':'','location':'','profile_pic':''})
        return jsonify(success=True,data={
            'name':p.get('full_name') or '','full_name':p.get('full_name') or '',
            'email':p.get('official_email') or '','official_email':p.get('official_email') or '',
            'mobile':p.get('mobile') or '','location':p.get('location') or '',
            'profile_pic':p.get('profile_pic') or ''
        })

    @bp.route('',methods=['PUT'])
    def upd_p():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        d=request.get_json(force=True) or {}
        name=(d.get('full_name') or '').strip()
        if not name: return jsonify(success=False,error='Name required'),400
        em=d.get('official_email') or ''; mob=d.get('mobile') or ''; loc=d.get('location') or ''
        if qone("SELECT id FROM admin_profile WHERE id=1"):
            exe("UPDATE admin_profile SET full_name=%s,official_email=%s,mobile=%s,location=%s WHERE id=1",(name,em,mob,loc))
        else:
            exe("INSERT INTO admin_profile(id,full_name,official_email,mobile,location) VALUES(1,%s,%s,%s,%s)",(name,em,mob,loc))
        exe("UPDATE users SET full_name=%s WHERE id=%s",(name,_uid()))
        session['uname']=name
        return jsonify(success=True)

    @bp.route('/photo',methods=['POST'])
    def photo():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        file=request.files.get('photo')
        if not file or not file.filename: return jsonify(success=False,error='No file'),400
        ext=file.filename.rsplit('.',1)[-1].lower() if '.' in file.filename else ''
        if ext not in ALLOWED_IMG: return jsonify(success=False,error='Invalid type'),400
        folder=os.path.join(current_app.config['UPLOAD_FOLDER'],'profiles')
        os.makedirs(folder,exist_ok=True); fn=secure_filename(file.filename)
        file.save(os.path.join(folder,fn))
        path=f'/static/uploads/profiles/{fn}'
        if qone("SELECT id FROM admin_profile WHERE id=1"):
            exe("UPDATE admin_profile SET profile_pic=%s WHERE id=1",(path,))
        else:
            exe("INSERT INTO admin_profile(id,profile_pic) VALUES(1,%s)",(path,))
        exe("UPDATE users SET profile_pic=%s WHERE id=%s",(path,_uid()))
        return jsonify(success=True,path=path,data={'photo_url':path})

    @bp.route('/change-password',methods=['PUT'])
    def change_pw():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        d=request.get_json(force=True) or {}
        curr=d.get('current_password') or ''; newp=d.get('new_password') or ''
        if not curr or not newp or len(newp)<6: return jsonify(success=False,error='Both passwords required'),400
        user=qone("SELECT password_hash FROM users WHERE id=%s",(_uid(),))
        if not user or not check_password_hash(user['password_hash'],curr):
            return jsonify(success=False,error='Current password incorrect'),403
        exe("UPDATE users SET password_hash=%s WHERE id=%s",(generate_password_hash(newp),_uid()))
        return jsonify(success=True)

    app.register_blueprint(bp)


# TEAM LEADERS
def _tl(app):
    bp=Blueprint('tl',__name__,url_prefix='/api/tl')
    def _s(t): return {
        'id':t['id'],'emp_id':t.get('emp_id') or '',
        'name':t.get('full_name') or '','full_name':t.get('full_name') or '',
        'email':t.get('email') or '','phone':t.get('phone') or '',
        'department':t.get('department') or '','experience':t.get('experience') or 0
    }

    @bp.route('',methods=['GET'])
    def list_tl():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        tl_rows = qall("SELECT id, emp_id, full_name, email, phone, department, experience FROM team_leaders ORDER BY id DESC")
        user_tls = qall("SELECT id, emp_id, full_name, official_email as email, mobile as phone, department, 0 as experience FROM users WHERE role='tl'")
        existing_emails = set(r.get('email','').lower() for r in tl_rows)
        for u in user_tls:
            if (u.get('email') or '').lower() not in existing_emails:
                tl_rows.append(u)
        return jsonify(success=True,data=[_s(r) for r in tl_rows])

    @bp.route('',methods=['POST'])
    def create_tl():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        d=request.get_json(force=True) or {}
        name=(d.get('full_name') or '').strip(); eid=(d.get('emp_id') or '').strip()
        if not name or not eid: return jsonify(success=False,error='full_name and emp_id required'),400
        if qone("SELECT id FROM team_leaders WHERE emp_id=%s",(eid,)):
            count=(qone("SELECT COUNT(*) AS c FROM team_leaders") or {}).get('c',0)
            eid=f"EMP-TL-{count+1:03d}"
        tid=exe("INSERT INTO team_leaders(emp_id,full_name,email,phone,department,experience) VALUES(%s,%s,%s,%s,%s,%s)",
            (eid,name,d.get('email') or '',d.get('phone') or '',d.get('department') or '',int(d.get('experience') or 0)))
        t=qone("SELECT * FROM team_leaders WHERE id=%s",(tid,))
        return jsonify(success=True,data=_s(t)),201

    @bp.route('/<int:tid>',methods=['PUT'])
    def update_tl(tid):
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        d=request.get_json(force=True) or {}
        exe("UPDATE team_leaders SET full_name=%s,email=%s,phone=%s,department=%s,experience=%s WHERE id=%s",
            (d.get('full_name'),d.get('email') or '',d.get('phone') or '',
             d.get('department') or '',int(d.get('experience') or 0),tid))
        t=qone("SELECT * FROM team_leaders WHERE id=%s",(tid,))
        return jsonify(success=True,data=_s(t) if t else {})

    @bp.route('/<int:tid>',methods=['DELETE'])
    def delete_tl(tid):
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        exe("DELETE FROM team_leaders WHERE id=%s",(tid,))
        return jsonify(success=True)

    app.register_blueprint(bp)


# DASHBOARD + SKILLS + NOTIFICATIONS
def _dashboard(app):
    bp=Blueprint('dashboard',__name__)

    @bp.route('/api/dashboard/stats',methods=['GET'])
    def stats():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        role = _urole()
        uid  = _uid()

        if role == 'pm':
            pm = qone('SELECT id FROM project_managers WHERE official_email=(SELECT official_email FROM users WHERE id=%s)', (uid,))
            pm_id = pm['id'] if pm else 0
            return jsonify(success=True,data={
                'active_projects': (qone("SELECT COUNT(*) AS c FROM projects WHERE assigned_pm_id=%s AND status NOT IN ('Completed','Overdue')", (pm_id,)) or {}).get('c',0),
                'pending_tasks':   (qone("SELECT COUNT(*) AS c FROM tasks t JOIN projects p ON t.project_id=p.id WHERE p.assigned_pm_id=%s AND t.status!='Completed'", (pm_id,)) or {}).get('c',0),
                'total_employees': (qone("SELECT COUNT(*) AS c FROM users WHERE role!='superadmin'") or {}).get('c',0),
                'total_pms':       (qone("SELECT COUNT(*) AS c FROM project_managers") or {}).get('c',0),
                'overdue_tasks':   (qone("SELECT COUNT(*) AS c FROM tasks t JOIN projects p ON t.project_id=p.id WHERE p.assigned_pm_id=%s AND t.deadline<CURDATE() AND t.status!='Completed'", (pm_id,)) or {}).get('c',0),
            })
        elif role == 'developer':
            user = qone("SELECT full_name FROM users WHERE id=%s", (uid,))
            uname = user['full_name'] if user else ''
            return jsonify(success=True,data={
                'active_projects': (qone("SELECT COUNT(DISTINCT project_id) AS c FROM tasks WHERE assigned_dev=%s AND status!='Completed'", (uname,)) or {}).get('c',0),
                'pending_tasks':   (qone("SELECT COUNT(*) AS c FROM tasks WHERE assigned_dev=%s AND status!='Completed'", (uname,)) or {}).get('c',0),
                'total_employees': 0,
                'total_pms':       0,
                'overdue_tasks':   (qone("SELECT COUNT(*) AS c FROM tasks WHERE assigned_dev=%s AND deadline<CURDATE() AND status!='Completed'", (uname,)) or {}).get('c',0),
            })
        elif role == 'tl':
            user = qone("SELECT full_name FROM users WHERE id=%s", (uid,))
            uname = user['full_name'] if user else ''
            return jsonify(success=True,data={
                'active_projects': (qone("SELECT COUNT(DISTINCT project_id) AS c FROM tasks WHERE assigned_tl=%s AND status!='Completed'", (uname,)) or {}).get('c',0),
                'pending_tasks':   (qone("SELECT COUNT(*) AS c FROM tasks WHERE assigned_tl=%s AND status!='Completed'", (uname,)) or {}).get('c',0),
                'total_employees': (qone("SELECT COUNT(*) AS c FROM users WHERE role='developer'") or {}).get('c',0),
                'total_pms':       0,
                'overdue_tasks':   (qone("SELECT COUNT(*) AS c FROM tasks WHERE assigned_tl=%s AND deadline<CURDATE() AND status!='Completed'", (uname,)) or {}).get('c',0),
            })
        else:
            return jsonify(success=True,data={
                'active_projects': (qone("SELECT COUNT(*) AS c FROM projects WHERE status NOT IN ('Completed','Overdue')") or {}).get('c',0),
                'pending_tasks':   (qone("SELECT COUNT(*) AS c FROM tasks WHERE status!='Completed'") or {}).get('c',0),
                'total_employees': (qone("SELECT COUNT(*) AS c FROM users WHERE role!='superadmin'") or {}).get('c',0),
                'total_pms':       (qone("SELECT COUNT(*) AS c FROM project_managers") or {}).get('c',0),
                'overdue_tasks':   (qone("SELECT COUNT(*) AS c FROM tasks WHERE deadline<CURDATE() AND status!='Completed'") or {}).get('c',0),
            })

    @bp.route('/api/skills',methods=['GET'])
    def skills():
        if not _uid(): return jsonify(success=False,error='Unauthorized'),401
        rows=qall("SELECT DISTINCT skills FROM users WHERE skills IS NOT NULL AND skills!=''")
        skill_set=set()
        for r in rows:
            for s in (r.get('skills') or '').split(','):
                s=s.strip()
                if s: skill_set.add(s)
        return jsonify(success=True,data=sorted(skill_set))

    @bp.route('/api/notifications',methods=['GET'])
    def notifs(): return jsonify(success=True,data=[],unread=0)

    @bp.route('/api/notifications/mark-read',methods=['POST'])
    def mark_read(): return jsonify(success=True)

    app.register_blueprint(bp)


# Module-level app object — required so gunicorn (which imports this file
# as a module, never running the __main__ block below) can find `app`
# via the standard `gunicorn app:app` command.
app = create_app()

if __name__ == '__main__':
    print('\n✅  TMS Enterprise → http://127.0.0.1:5000\n')
    app.run(debug=True, host='0.0.0.0', port=5000)