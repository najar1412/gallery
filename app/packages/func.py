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
        """makes a new session object.
        :param username: ...
        :param password: ...
        :return: bool
        :rtype: bool
        """
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
        """returns current session.
        :return: ...
        :rtype: dict
        """
        result = {}
        for k in self.session:
            result[k] = self.session[k]


        return result


    def filter(self, filter):
        """applied filter to current session.
        :param filter: ...
        :return: ...
        :rtype: ...
        """
        ALLOWED_FILTERS = ['gallery', 'nogallery']
        if filter not in ALLOWED_FILTERS:
            self.filter = None

        else:
            self.filter = filter


    def selection(self, snaps):
        """appends image to selection.
        :param snaps: ...
        :return: ...
        :rtype: ...
        """
        for snap_id in snaps:
            if snap_id in self.session['selection']:
                self.session['selection'].remove(str(snap_id))
                self.session.modified = True

            else:
                self.session['selection'].append(snap_id)
                self.session.modified = True


    def clear_selection(self):
        """clears image selections from current session.
        :return: ...
        :rtype: ...
        """
        self.session['selection'] = []


    def close(self):
        """closes current open session.
        :return: ...
        :rtype: ...
        """
        # TODO: remove any other attris in session
        self.session.pop('username', None)
        self.session.pop('user_name', None)
        self.session.pop('test', None)
        self.session.pop('filter', None)
        self.session.pop('selection', None)


# helpers
def allowed_file(filename):
    """check file to see if its of an allowed format.
    :param filename: ...
    :return: ...
    :rtype: ...
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.flask_allowed_extensions


def check_file_server(location, file):
    """checks if file is on the web server.
    :param location: ...
    :param file: ...
    :return: ...
    :rtype: ...
    """
    if os.path.isfile(os.path.join(location, file)):
        return file

    else:
        return False


def upload_to_server(location, file):
    """saves file from mem/tmp to web server.
    :param location: ...
    :param file: ...
    :return: ...
    :rtype: ...
    """
    if file.__dict__['filename'] != '':
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(location, filename))

            return filename

    else:
        pass


def rename_file(location, filename):
    """use uuid to rename uploaded files.
    :param location: ...
    :param filename: ...
    :return: ...
    :rtype: ...
    """
    name, ext = os.path.splitext(filename)
    new_uuid = str(uuid.uuid4())
    new_name = f'{new_uuid}{ext}'

    os.rename(os.path.join(location, filename), os.path.join(location, new_name))

    return new_name


def upload_to_s3(location, file):
    """moves file from web server to aws: s3.
    :param location: ...
    :param file: ...
    :return: ...
    :rtype: ...
    """
    s3 = boto3.client(
        's3',
        aws_access_key_id=config.aws_access_id,
        aws_secret_access_key=config.aws_secret_key,
    )

    s3.upload_file(os.path.join(location, file), config.aws_bucket, file)

    return file


def check_file_s3(file):
    """checks if file exists on aws: s3,
    :param file: ...
    :return: bool
    :rtype: bool
    """
    # TODO: imp checking of file on s3
    return True


def delete_file_server(location, file):
    """deletes file from web server.
    :param location: ...
    :param file: ...
    :return: bool
    :rtype: bool
    """
    try:
        os.remove(os.path.join(location, file))

        return True

    except:
        print(f'deleting of {file} failed.')

        return False


def delete_file_s3(file):
    """deletes file from aws: s3.
    :param file: ...
    :return: bool
    :rtype: bool
    """
    s3 = boto3.client(
        's3',
        aws_access_key_id=config.aws_access_id,
        aws_secret_access_key=config.aws_secret_key,
    )

    s3.delete_object(Bucket=config.aws_bucket, Key=file)

    return True


def file_handler(location, files):
    """takes files from web app, processes and uploads to aws: s3.
    :param location: ...
    :param files: ...
    :return: ...
    :rtype: list
    """
    filenames = []
    for file in files:
        original_file = upload_to_server(location, file)
        check_file = check_file_server(location, original_file)

        if check_file:
            renamed_file = rename_file(location, check_file)
            upload_to_s3(location, renamed_file)

            if check_file_s3:
                delete_file_server(location, renamed_file)
            filenames.append(renamed_file)
            
        else:
            print('file does not exist')

    return filenames
