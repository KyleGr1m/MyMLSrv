from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import re
from functools import wraps

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'txt'}
app.secret_key = 'your_secret_key_here'
app.config['SESSION_TYPE'] = 'filesystem'  # Add this line

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'Verxes' and password == '272504':
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return "Invalid credentials", 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def parse_file(content):
    accounts = []
    for line in content.splitlines():
        if ':' in line:
            parts = line.split(':', 1)
            email = parts[0].strip()
            rest = parts[1].split('|')
            password = rest[0].strip()
            
            # Extract clean UID
            uid_match = re.search(r'RoleID:\s*(\d+)', line) or re.search(r'UID:\s*(\d+)', line)
            uid = uid_match.group(1) if uid_match else ''
            
            # Create full info string in requested format
            full_info = f"{email}:{password} | {' | '.join([p.strip() for p in rest[1:]])}"
            
            accounts.append({
                'email': email,
                'password': password,
                'uid': uid,
                'full_info': full_info,
                'details': ' | '.join([p.strip() for p in rest[1:]])
            })
    return accounts

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            content = file.read().decode('utf-8')
            accounts = parse_file(content)
            session['accounts'] = accounts  # Store in session for pagination
            return redirect(url_for('view_accounts', page=1))
    return render_template('index.html')

@app.route('/accounts/<int:page>')
@login_required
def view_accounts(page):
    if 'accounts' not in session:
        flash('No accounts found. Please upload a file first.', 'error')
        return redirect(url_for('index'))
    
    accounts = session.get('accounts', [])
    per_page = 50
    total_pages = max(1, (len(accounts) + per_page - 1) // per_page)  # Fixed calculation
    
    # Validate page number
    if page < 1 or (total_pages > 0 and page > total_pages):
        flash('Invalid page number', 'error')
        return redirect(url_for('view_accounts', page=1))
    
    start = (page - 1) * per_page
    end = start + per_page
    paginated_accounts = accounts[start:end]
    
    return render_template('results.html', 
                         accounts=paginated_accounts,
                         current_page=page,
                         total_pages=total_pages,
                         total_accounts=len(accounts))

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
