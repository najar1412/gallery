import json

from flask import Flask, render_template, request, session, redirect, url_for, escape
import requests
from requests.auth import HTTPBasicAuth


app = Flask(__name__)
app.secret_key = 'SPECIALSECRETKEYWHAAA'

BASEURL = 'http://127.0.0.1:5050/gallery/v1'


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


@app.route('/')
def index():
    if 'user_email' in session:
        bla = 'Logged in as %s' % escape(session['user_email'])
        username = 'r@r.com'
        password = 'r'

        r = requests.get('{}/accounts'.format(BASEURL), auth=HTTPBasicAuth('r@r.com', 'r'))
        print(r.json())


        return render_template('index.html', bla=bla)

    return redirect(url_for('login'))


@app.route('/galleries')
def galleries():
    if 'user_email' in session:
        bla = 'Logged in as %s' % escape(session['user_email'])

        r = requests.get('{}/galleries'.format(BASEURL), auth=HTTPBasicAuth('r@r.com', 'r'))
        response = r.json()
        if response['status']:
            if response['status'] == 'success':
                galleries = response['data']
            else:
                galleries = []
        else:
            galleries = []

        return render_template('galleries.html', galleries=galleries, bla=bla)

    else:
        return redirect(url_for('login'))


@app.route('/gallery/<int:id>')
def gallery(id):
    if 'user_email' in session:
        r = requests.get('{}/galleries/{}'.format(BASEURL, id), auth=HTTPBasicAuth('r@r.com', 'r'))
        response = r.json()
        if response['status']:
            if response['status'] == 'success':
                gallery = response['data']
            else:
                gallery = []
        else:
            gallery = []

        return render_template('gallery.html', gallery=gallery)

    else:
        return redirect(url_for('login'))


@app.route('/upload')
def upload():
    return render_template('upload.html')


@app.route('/settings')
def settings():
    return render_template('settings.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
