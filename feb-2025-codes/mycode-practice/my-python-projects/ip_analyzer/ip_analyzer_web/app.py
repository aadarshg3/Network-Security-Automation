from flask import Flask, render_template, request
from ip_utils import analyze_ip

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = ''
    if request.method == 'POST':
        ip_address = request.form['ip_address']
        result = analyze_ip(ip_address)
    return render_template('index.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)

