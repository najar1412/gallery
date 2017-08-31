import json

from flask import Flask, render_template, request, session, redirect, url_for, escape
import requests
from requests.auth import HTTPBasicAuth

from packages import func


app = Flask(__name__)
app.secret_key = 'SPECIALSECRETKEYWHAAA'

BASEURL = 'http://127.0.0.1:5050/gallery/v1'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if 'Login' in request.form:
            new_login = func.SessionHandler(session).new(request.form['username'], request.form['password'])
            if new_login:

                return redirect(url_for('index'))

            else:
                print('no cred')
                return redirect(url_for('login'))

        elif 'Signup' in request.form:
            username = request.form['username']
            password = request.form['password']

            # TODO: Imp input and database checking.
            r = requests.post(f'{BASEURL}/accounts?username={username}&password={password}')
            session['username'] = username

            return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    # remove the username from the session if it's there

    # session.pop('username', None)
    user = func.SessionHandler(session).close()

    return redirect(url_for('index'))


@app.route('/')
def index():
    if 'username' in session:
        bla = 'Logged in as %s' % escape(session['username'])

        # r = requests.get('{}/accounts'.format(BASEURL), auth=HTTPBasicAuth('r@r.com', 'r'))


        return render_template('index.html', bla=bla)

    return redirect(url_for('login'))


@app.route('/galleries')
def galleries():
    if 'username' in session:
        bla = 'Logged in as %s' % escape(session['username'])

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
    if 'username' in session:
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


@app.route('/new_gallery', methods=['GET', 'POST'])
def new_gallery():
    print('new gallery')
    return redirect(url_for('galleries'))


@app.route('/upload')
def upload():
    return render_template('upload.html')


@app.route('/settings')
def settings():
    return render_template('settings.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
