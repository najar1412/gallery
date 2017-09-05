import json
import os
import pathlib

from flask import Flask, render_template, request, session, redirect, url_for, abort
import requests
from requests.auth import HTTPBasicAuth

from config import config
from packages import func


# TODO: UPloading anything other than a jpg is an error.

# Flask config
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    config.flask_upload_folder
    )
app.secret_key = config.flask_secret_key


# flask errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('/error/404.html'), 404


# Flask routes
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
        r = requests.get(
            '{}/accounts'.format(config.BASEURL),
            auth=HTTPBasicAuth(user['username'], user['password'])
            )
        response = r.json()

        if 'status' in response and response['status'] == 'success':
            snaps = response['data'][0]['snaps']

        return render_template('index.html', user=user)

    return redirect(url_for('login'))


@app.route('/share/<uuid>')
def share(uuid):
    # TODO: IMP gallery sharing route
    gallery = requests.get(f'{config.BASEURL}/shareuuid/{uuid}').json()

    if 'status' in gallery and gallery['status'] == 'success':
        gallery = [snap for snap in gallery['data'] if snap['private'] != True]

        return render_template('share.html', gallery=gallery)

    else:
        return abort(404)


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


@app.route('/snaps')
def snaps():
    user = func.SessionHandler(session).get()
    if 'username' in user:
        r = requests.get(
            '{}/snaps'.format(config.BASEURL),
            auth=HTTPBasicAuth(user['username'], user['password'])
            )
        response = r.json()

        if response['status']:
            if response['status'] == 'success':
                snaps = response['data']

            else:
                snaps = []

        else:
            snaps = []

        return render_template('snaps.html', snaps=snaps, user=user)

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

        return render_template('gallery.html', gallery=gallery, user=user, gallery_id=id)

    else:
        return redirect(url_for('login'))


@app.route('/new_gallery', methods=['GET', 'POST'])
def new_gallery():
    user = func.SessionHandler(session).get()
    title = request.form['title']
    files_to_upload = request.files.getlist("upload")

    # check if there are any files in the request.
    if len(files_to_upload) == 1 and files_to_upload[0].__dict__['filename'] == '':
        uploaded_files = False
    else:
        uploaded_files = func.file_handler(app.config['UPLOAD_FOLDER'], files_to_upload)
        print(uploaded_files)

    r = requests.post(
        '{}/galleries?title={}'.format(config.BASEURL, title),
        auth=HTTPBasicAuth(user['username'], user['password'])
        )

    if uploaded_files and r.json()['status'] == 'success':
        gallery_id = r.json()['data'][0]['id']
        for x in uploaded_files:

            post_snap = requests.post(
                '{}/snaps?name={}'.format(config.BASEURL, x),
                auth=HTTPBasicAuth(user['username'], user['password'])
                ).json()

            if 'status' in post_snap and post_snap['status'] == 'success':
                snaps_id = post_snap['data'][0]['id']
                requests.put(
                    f'{config.BASEURL}/galleries/{gallery_id}?snaps={snaps_id}',
                    auth=HTTPBasicAuth(user['username'], user['password'])
                    )

        return redirect(f'gallery/{gallery_id}')

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

    return redirect(url_for('galleries'))


@app.route('/new_snap', methods=['GET', 'POST'])
def new_snap():
    user = func.SessionHandler(session).get()
    files_to_upload = request.files.getlist("upload")

    try:
        print('try')
        gallery_id = request.form['gallery']
    except:
        print('except')
        gallery_id = None

    if len(files_to_upload) == 1 and files_to_upload[0].__dict__['filename'] == '':
        uploaded_files = False
    else:
        uploaded_files = func.file_handler(app.config['UPLOAD_FOLDER'], files_to_upload)
        print(uploaded_files)

    if files_to_upload:
        for x in uploaded_files:
            post_snap = requests.post(
                '{}/snaps?name={}'.format(config.BASEURL, x),
                auth=HTTPBasicAuth(user['username'], user['password'])
                ).json()

            if 'status' in post_snap and post_snap['status'] == 'success':
                snaps_id = post_snap['data'][0]['id']
                requests.put(
                    f'{config.BASEURL}/galleries/{gallery_id}?snaps={snaps_id}',
                    auth=HTTPBasicAuth(user['username'], user['password'])
                    )

    if gallery_id:
        return redirect(f'gallery/{gallery_id}')
    else:
        return redirect('snaps')


@app.route('/edit_snap/<int:id>', methods=['GET', 'POST'])
def edit_snap(id):
    user = func.SessionHandler(session).get()
    args = dict(request.form)
    # if try passes request was from a gallery
    # except means request was from a snap
    try:
        gallery_id = args['gallery'][0]
    except:
        print('its a none')
        gallery_id = None

    if 'private' in args:
        requests.put(
            '{}/snaps/{}?private=string'.format(config.BASEURL, id),
            auth=HTTPBasicAuth(user['username'], user['password'])
            )

    elif 'transform' in args:
        print('transform clickd')

    elif 'delete' in args:
        print('deleting.................')
        snap = requests.get('{}/snaps/{}'.format(config.BASEURL, id),
        auth=HTTPBasicAuth(user['username'], user['password'])
        ).json()

        test_snap = requests.get('{}/accounts'.format(config.BASEURL),
        auth=HTTPBasicAuth(user['username'], user['password'])
        ).json()

        print(test_snap)

        if 'status' in snap and snap['status'] == 'success':
            snap_name = snap['data'][0]['name']

            delete_from_s3 = func.delete_file_s3(snap_name)
            if delete_from_s3:
                requests.delete(
                    '{}/snaps/{}'.format(config.BASEURL, id),
                    auth=HTTPBasicAuth(user['username'], user['password'])
                    )
            else:
                print('Deleting {} from s3 failed.')

    if gallery_id:
        return redirect(f'gallery/{gallery_id}')
    else:
        return redirect('snaps')


@app.route('/settings')
def settings():
    user = func.SessionHandler(session).get()
    return render_template('settings.html', user=user)


@app.route('/privacy')
def privacy():
    user = func.SessionHandler(session).get()
    return render_template('privacy.html', user=user)


@app.route('/terms')
def terms():
    user = func.SessionHandler(session).get()
    return render_template('terms.html', user=user)


@app.route('/contact')
def contact():
    user = func.SessionHandler(session).get()
    return render_template('contact.html', user=user)


@app.route('/about')
def about():
    user = func.SessionHandler(session).get()
    return render_template('about.html', user=user)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
