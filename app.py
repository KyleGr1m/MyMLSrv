from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'txt'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def parse_file(content):
    accounts = []
    for line in content.splitlines():
        if ':' in line:
            parts = line.split(':', 1)
            email = parts[0].strip()
            rest = parts[1].split('|')
            password = rest[0].strip()
            details = ' | '.join(rest[1:]).strip()
            accounts.append({
                'email': email,
                'password': password,
                'details': details
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
    app.run(debug=True)
