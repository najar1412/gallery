import json
import os
import pathlib

from flask import Flask, render_template, request, session, redirect, url_for, escape
import requests
from requests.auth import HTTPBasicAuth

from config import config
from packages import func

# Flask config
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    config.flask_upload_folder
    )
app.secret_key = config.flask_secret_key

# Flask routes
@app.route('/upload', methods=['POST', "GET"])
def upload():
    files_to_upload = request.files.getlist("upload")
    uploaded_files = func.file_handler(app.config['UPLOAD_FOLDER'], files_to_upload)

    return redirect(url_for('galleries'))


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
                    f'{config.BASEURL}/accounts?username={username}&password={password}'
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


@app.route('/share/<uuid>')
def share(uuid):
    # TODO: IMP gallery sharing route
    gallery = requests.get(f'{config.BASEURL}/shareuuid/{uuid}').json()['data']
    return render_template('share.html', gallery=gallery)


@app.route('/galleries')
def galleries():
    user = func.SessionHandler(session).get()

    if 'username' in user:
        r = requests.get(
            '{}/galleries'.format(config.BASEURL),
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
            '{}/galleries/{}'.format(config.BASEURL, id),
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
        '{}/galleries?title={}'.format(config.BASEURL, title),
        auth=HTTPBasicAuth(user['username'], user['password'])
        )

    return redirect(url_for('galleries'))


@app.route('/edit_gallery/<int:id>', methods=['GET', 'POST'])
def edit_gallery(id):
    user = func.SessionHandler(session).get()
    args = dict(request.form)

    if 'private' in args:
        requests.put(
            '{}/galleries/{}?private=string'.format(config.BASEURL, id),
            auth=HTTPBasicAuth(user['username'], user['password'])
            )

    elif 'edit' in args:
        print('edit clickd')

    elif 'delete' in args:
        requests.delete(
            '{}/galleries/{}'.format(config.BASEURL, id),
            auth=HTTPBasicAuth(user['username'], user['password'])
            )
        print('delete clciked')

    return redirect(url_for('galleries'))


@app.route('/new_snap', methods=['GET', 'POST'])
def new_snap():
    user = func.SessionHandler(session).get()
    title = request.form['title']
    gallery_id = request.form['gallery']

    post_snap = requests.post(
        '{}/snaps?title={}'.format(config.BASEURL, title),
        auth=HTTPBasicAuth(user['username'], user['password'])
        ).json()

    if 'status' in post_snap and post_snap['status'] == 'success':
        snaps_id = post_snap['data'][0]['id']
        requests.put(
            f'{config.BASEURL}/galleries/{gallery_id}?snaps={snaps_id}',
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
