import json
import os
import pathlib

from flask import Flask, render_template, request, session, redirect, url_for, abort
import requests
from requests.auth import HTTPBasicAuth

from config import config
from packages import func


# TODO: UPloading anything other than a jpg is an error.
# TODO: on dev rebuilding the database if user has redicentuals still in session
# user can still up load to s3, strange bug.

# Flask config
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    config.flask_upload_folder
    )
app.secret_key = config.flask_secret_key

# build themes
# default theme
test = requests.get('{}/themes'.format(config.BASEURL))
if test.status_code == 200:
    pass
else:
    requests.post(
        '{}/themes?name=default'.format(config.BASEURL))
    requests.post(
        '{}/themes?name=polaroid'.format(config.BASEURL))
    requests.post(
        '{}/themes?name=slide'.format(config.BASEURL))


@app.route('/temptest')
def temptest():
    """use for testing themes"""
    return render_template('theme/slide.html')


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
        snaps = [snap for snap in gallery['data']['snaps'] if snap['private'] != True]
        theme_name = gallery['data']['theme'][0]['name']
        theme_exists = func.check_file_server(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'templates', 'theme'
            ), f"{theme_name}.html")

        if theme_exists:
            return render_template('theme/{}.html'.format(theme_name), gallery=snaps)


        elif theme_exists == False:
            return render_template('theme/default.html'.format(theme_name), gallery=snaps)


        else:
            print(f"Theme {theme_name} does not exist.")

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

                themes = requests.get(
                    '{}/themes'.format(config.BASEURL)
                    )

                if themes.status_code == 200:
                    if 'status' in themes.json() and themes.json()['status'] == 'success':
                        get_themes = themes.json()['data']
                else:
                    get_themes = []

            else:
                get_themes = []
                galleries = []

        else:
            get_themes = []
            galleries = []

        return render_template('galleries.html', galleries=galleries, themes=get_themes, user=user)


    else:
        return redirect(url_for('login'))


@app.route('/batches')
def batches():
    user = func.SessionHandler(session).get()
    if 'username' in user:
        r = requests.get(
            '{}/batches'.format(config.BASEURL),
            auth=HTTPBasicAuth(user['username'], user['password'])
            )

        response = r.json()

        if response['status']:
            if response['status'] == 'success':
                batches = response['data']

            else:
                batches = []

        else:
            batches = []

        return render_template('batches.html', batches=batches, user=user)


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


@app.route('/batch/<int:id>')
def batch(id):
    user = func.SessionHandler(session).get()
    if 'username' in user:
        response = requests.get(
            '{}/batches/{}'.format(config.BASEURL, id),
            auth=HTTPBasicAuth(user['username'], user['password'])
            ).json()
        if response['status']:
            if response['status'] == 'success':
                batch = response['data']
                print('oooooooooooooooooooooooooo')
                print(batch)

            else:
                batch = []
        else:
            batch = []

        return render_template('batch.html', batch=batch, user=user, batch_id=id)

    else:
        return redirect(url_for('login'))


@app.route('/new_gallery', methods=['GET', 'POST'])
def new_gallery():
    user = func.SessionHandler(session).get()
    args = dict(request.form)
    
    if 'clear_selection' in args and args['clear_selection'][0] == 'True':
        print('clearing selection')
        func.SessionHandler(session).clear_selection()

        return redirect('/galleries')

    # check if there are selected snaps for new gallery
    if 'selection' not in args:
        selection = ''
    else:
        selection = ' '.join(session['selection'])

    r = requests.post(
        '{}/galleries?title={}&snaps={}'.format(config.BASEURL, args['title'][0], selection),
        auth=HTTPBasicAuth(user['username'], user['password'])
        )

    if r.json()['status'] == 'success':
        gallery_id = r.json()['data'][0]['id']

        # append selected snaps to new gallery

        return redirect(f'gallery/{gallery_id}')


    return redirect(url_for('galleries'))


@app.route('/new_batch', methods=['GET', 'POST'])
def new_batch():
    user = func.SessionHandler(session).get()
    title = request.form['title']
    files_to_upload = request.files.getlist("upload")

    # check if there are any files in the request.
    if len(files_to_upload) == 1 and files_to_upload[0].__dict__['filename'] == '':
        uploaded_files = False
    else:
        uploaded_files = func.file_handler(app.config['UPLOAD_FOLDER'], files_to_upload)

    r = requests.post(
        '{}/batches?title={}'.format(config.BASEURL, title),
        auth=HTTPBasicAuth(user['username'], user['password'])
        )

    if uploaded_files and r.json()['status'] == 'success':
        batch_id = r.json()['data'][0]['id']
        
        for x in uploaded_files:
            post_snap = requests.post(
                '{}/snaps?name={}&snap_original={}&snap_lores={}&snap_thumb={}'.format(config.BASEURL, x, x, x, x),
                auth=HTTPBasicAuth(user['username'], user['password'])
                ).json()

            if 'status' in post_snap and post_snap['status'] == 'success':
                snaps_id = post_snap['data'][0]['id']
                requests.put(
                    f'{config.BASEURL}/batches/{batch_id}?snaps={snaps_id}',
                    auth=HTTPBasicAuth(user['username'], user['password'])
                    )
           
        return redirect(f'batch/{batch_id}')

    return redirect(url_for('batches'))


@app.route('/edit_gallery/<int:id>', methods=['GET', 'POST'])
def edit_gallery(id):
    user = func.SessionHandler(session).get()
    args = dict(request.form)

    if 'private' in args:
        requests.put(
            '{}/galleries/{}?private=string'.format(config.BASEURL, id),
            auth=HTTPBasicAuth(user['username'], user['password'])
            )

    if 'changed_theme' in args:
        get_theme = requests.get(f'{config.BASEURL}/themes/{args["changed_theme"][0]}')
        if get_theme.status_code == 200:
            theme_name = str(get_theme.json()['data'][0]['name'])
            requests.put(
                f'{config.BASEURL}/galleries/{id}?theme={theme_name}',
                auth=HTTPBasicAuth(user['username'], user['password'])
                )
        else:
            pass

    if 'snap_id' in args:
        requests.put(
            f'{config.BASEURL}/galleries/{id}?snaps={args["snap_id"][0]}',
            auth=HTTPBasicAuth(user['username'], user['password'])
            )

    if 'edit' in args:
        print('edit clickd')

    if 'delete' in args:
        requests.delete(
            '{}/galleries/{}'.format(config.BASEURL, id),
            auth=HTTPBasicAuth(user['username'], user['password'])
            )

    return redirect(url_for('galleries'))


@app.route('/edit_batch/<int:id>', methods=['GET', 'POST'])
def edit_batch(id):
    user = func.SessionHandler(session).get()
    args = dict(request.form)

    if 'snap_id' in args:
        # TODO: IMP
        requests.put(
            f'{config.BASEURL}/galleries/{id}?snaps={args["snap_id"][0]}',
            auth=HTTPBasicAuth(user['username'], user['password'])
            )

    if 'edit' in args:
        print('edit clickd')

    if 'delete' in args:
        requests.delete(
            '{}/batches/{}'.format(config.BASEURL, id),
            auth=HTTPBasicAuth(user['username'], user['password'])
            )

    return redirect(url_for('batches'))


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

    elif 'select' in args:
        print(args)
        add_selection = func.SessionHandler(session).selection(args['select'])

    elif 'delete' in args:
        print('deleting.................')
        snap = requests.get('{}/snaps/{}'.format(config.BASEURL, id),
        auth=HTTPBasicAuth(user['username'], user['password'])
        ).json()

        if 'status' in snap and snap['status'] == 'success':
            snap_name = snap['data'][0]['snap_original']

            delete_from_s3 = func.delete_file_s3(snap_name)
            if delete_from_s3:
                requests.delete(
                    '{}/snaps/{}'.format(config.BASEURL, id),
                    auth=HTTPBasicAuth(user['username'], user['password'])
                    )
            else:
                print('Deleting {} from s3 failed.')

            if 'batch' in args and args['batch'] != '':
                print('REALLY?!')
                return redirect(f'batch/{args["batch"][0]}')

    if gallery_id:
        return redirect(f'gallery/{gallery_id}')
    else:
        return redirect(f'batch/{args["batch"][0]}')


@app.route('/filter', methods=['GET', 'POST'])
def fitler(filter):
    user = func.SessonHandler(session).get()
    if user:
        func.SessionHandler(session).filter(filter)


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
