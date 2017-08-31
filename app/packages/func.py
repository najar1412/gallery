import requests
from requests.auth import HTTPBasicAuth

from config import config


class SessionHandler():
    def __init__(self, session):
        self.session = session

    def new(self, username, password):
        # TODO: request returns all login details, security issue.
        # make api route that just returns True/False.
        r = requests.get('{}/accounts'.format(config.BASEURL), auth=HTTPBasicAuth(username, password))

        if r.status_code == 200:
            self.session['username'] = username
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

    def close(self):
        # TODO: remove any other attris in session
        self.session.pop('username', None)
        self.session.pop('user_name', None)
        self.session.pop('test', None)
