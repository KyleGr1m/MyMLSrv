from flask import Flask, render_template, request, redirect, url_for
import os
import re

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'txt'}

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
            uid_match = re.search(r'UID:\s*(\d+)', line)
            uid = uid_match.group(1) if uid_match else ''
            
            # Extract other details
            details = []
            for part in rest[1:]:
                part = part.strip()
                if not part.startswith('UID:'):
                    details.append(part)
            
            accounts.append({
                'email': email,
                'password': password,
                'uid': uid,
                'details': ' | '.join(details),
                'full_info': f"Email: {email}\nPassword: {password}\nUID: {uid}\nDetails: {' | '.join(details)}"
            })
    return accounts

@app.route('/', methods=['GET', 'POST'])
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
            return render_template('results.html', accounts=accounts)
    return render_template('index.html')

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
