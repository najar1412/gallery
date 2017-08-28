import json

from flask import Flask, render_template, request, session, redirect, url_for, escape
import requests
from requests.auth import HTTPBasicAuth


app = Flask(__name__)
app.secret_key = 'SPECIALSECRETKEYWHAAA'

BASEURL = 'http://127.0.0.1:5050/gallery/v1'


@app.route('/')
def index():
    if 'user_email' in session:

        bla = 'Logged in as %s' % escape(session['user_email'])

        return render_template('index.html', bla=bla)

    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if 'Login' in request.form:
            session['user_email'] = request.form['user_email']

            return redirect(url_for('index'))

        elif 'Signup' in request.form:
            user_email = request.form['user_email']
            user_pass = request.form['user_pass']

            # TODO: Imp input and database checking.
            r = requests.post(f'{BASEURL}/accounts?username={user_email}&password={user_pass}')
            session['user_email'] = user_email

            return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    # remove the user_email from the session if it's there
    session.pop('user_email', None)

    return redirect(url_for('index'))



"""
@app.route('/')
def home():
    accounts = {}
    galleries = {}
    snaps = {}

    r = requests.get('{}/accounts'.format(BASEURL), auth=HTTPBasicAuth('admin', 'admin'))
    print(r.json())

    return render_template('index.html', accounts=accounts, galleries=galleries, snaps=snaps)
"""

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

"""



"""
