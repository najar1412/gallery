import os
import os.path
import uuid

import requests
from requests.auth import HTTPBasicAuth
from werkzeug import secure_filename
import boto3

from config import config


class SessionHandler():
    def __init__(self, session):
        self.session = session

    def new(self, username, password):
        # TODO; should password be stored in session? sec issue?
        # TODO: request returns all login details, security issue.
        # make api route that just returns True/False.
        r = requests.get('{}/accounts'.format(config.BASEURL), auth=HTTPBasicAuth(username, password))

        if r.status_code == 200:
            self.session['username'] = username
            self.session['password'] = password
            self.session['filter'] = None
            self.session['selection'] = []
            return True

        elif r.status_code == 401:
            print('NO ACCESS, 401')
            return False

        else:
            print('some other error')
            print(r.status_code)
            return False

    def get(self):
        result = {}
        for k in self.session:
            result[k] = self.session[k]


        return result

    def filter(self, filter):
        ALLOWED_FILTERS = ['gallery', 'nogallery']
        if filter not in ALLOWED_FILTERS:
            self.filter = None
        else:
            self.filter = filter

    def selection(self, snaps):
        for snap_id in snaps:
            if snap_id in self.session['selection']:
                print(snap_id)
                print(self.session['selection'])
                self.session['selection'].remove(str(snap_id))
                self.session.modified = True
            else:
                print(snap_id)
                print(self.session['selection'])
                self.session['selection'].append(snap_id)
                self.session.modified = True

        print(self.session['selection'])

    def clear_selection(self):
        self.session['selection'] = []


    def close(self):
        # TODO: remove any other attris in session
        self.session.pop('username', None)
        self.session.pop('user_name', None)
        self.session.pop('test', None)
        self.session.pop('filter', None)
        self.session.pop('selection', None)


# helpers
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.flask_allowed_extensions


def check_file_server(location, file):
    if os.path.isfile(os.path.join(location, file)):
        return file
    else:
        return False


def upload_to_server(location, file):
    if file.__dict__['filename'] != '':
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(location, filename))

            return filename

    else:
        pass


def rename_file(location, filename):
    name, ext = os.path.splitext(filename)
    new_uuid = str(uuid.uuid4())
    new_name = f'{new_uuid}{ext}'

    os.rename(os.path.join(location, filename), os.path.join(location, new_name))

    return new_name


def upload_to_s3(location, file):
    s3 = boto3.client(
        's3',
        aws_access_key_id=config.aws_access_id,
        aws_secret_access_key=config.aws_secret_key,
    )

    s3.upload_file(os.path.join(location, file), config.aws_bucket, file)

    return file


def check_file_s3(file):
    # TODO: imp checking of file on s3
    return True


def delete_file_server(location, file):
    try:
        os.remove(os.path.join(location, file))
        return True
    except:
        print(f'deleting of {file} failed.')
        return False


def delete_file_s3(file):
    s3 = boto3.client(
        's3',
        aws_access_key_id=config.aws_access_id,
        aws_secret_access_key=config.aws_secret_key,
    )

    s3.delete_object(Bucket=config.aws_bucket, Key=file)

    return True


def file_handler(location, files):
    filenames = []
    for file in files:
        # upload file to server
        original_file = upload_to_server(location, file)
        # check that file exists after upload to server
        check_file = check_file_server(location, original_file)
        # rename file
        if check_file:
            renamed_file = rename_file(location, check_file)
            # upload new file to s3
            upload_to_s3(location, renamed_file)
            if check_file_s3:
                delete_file_server(location, renamed_file)
            # return list of new files
            filenames.append(renamed_file)
        else:
            print('file does not exist')

    return filenames
