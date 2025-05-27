from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_session import Session
import os
import re
from functools import wraps

app = Flask(__name__)
app.secret_key = 'VXES'

# File upload settings
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'txt'}

# Session config for Render
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'
app.config['SESSION_PERMANENT'] = False
Session(app)

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
        line = line.strip()
        if not line or ':' not in line:
            continue
        try:
            email_part, rest = line.split(':', 1)
            email = email_part.strip()
            parts = rest.split('|', 1)
            password = parts[0].strip()
            details = parts[1].strip() if len(parts) > 1 else ''

            uid = ''
            role_match = re.search(r'RoleID:\s*(\d+)', line)
            uid_match = re.search(r'UID:\s*(\d+)', line)
            if role_match:
                uid = role_match.group(1)
            elif uid_match:
                uid = uid_match.group(1)

            accounts.append({
                'email': email,
                'password': password,
                'uid': uid,
                'full_info': line,
                'details': details
            })
        except Exception as e:
            print(f"Error parsing line: {line}\nError: {str(e)}")
            continue
    return accounts

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            try:
                content = file.read().decode('utf-8')
                accounts = parse_file(content)

                if not accounts:
                    flash('No valid accounts found in the file', 'error')
                    return redirect(request.url)

                session['accounts'] = accounts
                flash(f'Successfully loaded {len(accounts)} accounts', 'success')
                return redirect(url_for('view_accounts', page=1))

            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'error')
                return redirect(request.url)

    return render_template('index.html')

@app.route('/accounts/<int:page>')
@login_required
def view_accounts(page):
    if 'accounts' not in session:
        flash('No accounts found. Please upload a file first.', 'error')
        return redirect(url_for('index'))

    accounts = session['accounts']
    per_page = 50
    total_pages = max(1, (len(accounts) + per_page - 1) // per_page)

    if page < 1 or page > total_pages:
        page = 1

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
