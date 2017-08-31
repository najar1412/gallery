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
        if 'login' in request.form:
            check_auth = func.SessionHandler(session).new(
                request.form['username'], request.form['password']
                )
            if check_auth:
                return redirect(url_for('index'))

            else:
                return redirect(url_for('login'))

        elif 'signup' in request.form:
            username = request.form['username']
            password = request.form['password']
            account_exists = func.SessionHandler(session).new(username, password)
            if account_exists:
                print('accounts exists, return to login page')
                return redirect(url_for('login'))

            else:
                print('make new account')
                r = requests.post(
                    f'{BASEURL}/accounts?username={username}&password={password}'
                    )
                func.SessionHandler(session).new(username, password)
                return redirect(url_for('index'))

    else:
        return render_template('login.html')


@app.route('/logout')
def logout():
    user = func.SessionHandler(session).close()
    return redirect(url_for('index'))


@app.route('/')
def index():
    user = func.SessionHandler(session).get()
    if 'username' in user:
        return render_template('index.html', user=user)

    return redirect(url_for('login'))


@app.route('/galleries')
def galleries():
    user = func.SessionHandler(session).get()

    if 'username' in user:
        r = requests.get(
            '{}/galleries'.format(BASEURL),
            auth=HTTPBasicAuth(user['username'], user['password'])
            )
        response = r.json()

        if response['status']:
            if response['status'] == 'success':
                galleries = response['data']

            else:
                galleries = []

        else:
            galleries = []

        return render_template('galleries.html', galleries=galleries, user=user)

    else:
        return redirect(url_for('login'))


@app.route('/gallery/<int:id>')
def gallery(id):
    user = func.SessionHandler(session).get()
    if 'username' in user:
        response = requests.get(
            '{}/galleries/{}'.format(BASEURL, id),
            auth=HTTPBasicAuth(user['username'], user['password'])
            ).json()
        if response['status']:
            if response['status'] == 'success':
                gallery = response['data']
            else:
                gallery = []
        else:
            gallery = []

        return render_template('gallery.html', gallery=gallery, user=user)

    else:
        return redirect(url_for('login'))


@app.route('/new_gallery', methods=['GET', 'POST'])
def new_gallery():
    user = func.SessionHandler(session).get()
    title = request.form['title']

    r = requests.post(
        '{}/galleries?title={}'.format(BASEURL, title),
        auth=HTTPBasicAuth(user['username'], user['password'])
        )

    return redirect(url_for('galleries'))


@app.route('/new_snap', methods=['GET', 'POST'])
def new_snap():
    user = func.SessionHandler(session).get()
    title = request.form['title']
    gallery_id = request.form['gallery']

    post_snap = requests.post(
        '{}/snaps?title={}'.format(BASEURL, title),
        auth=HTTPBasicAuth(user['username'], user['password'])
        ).json()

    if 'status' in post_snap and post_snap['status'] == 'success':
        snaps_id = post_snap['data'][0]['id']
        requests.put(
            f'{BASEURL}/galleries/{gallery_id}?snaps={snaps_id}',
            auth=HTTPBasicAuth(user['username'], user['password'])
            )

        return redirect(f'gallery/{gallery_id}')

    else:
        return render_template('index.html', user=user)


@app.route('/settings')
def settings():
    user = func.SessionHandler(session).get()
    return render_template('settings.html', user=user)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
