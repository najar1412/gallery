import requests
from requests.auth import HTTPBasicAuth

from config import config


class SessionHandler():
    def __init__(self, session):
        self.session = session

    def new(self, username, password):
        # TODO: this is a mess
        """
        if self.session['username']:
            # if username in database
            # check password
            # error check
            # return session
            # else add new user and password to database
            pass
        """

        r = requests.get('{}/accounts'.format(config.BASEURL), auth=HTTPBasicAuth(username, password))

        try:
            print(r.json())
            self.session['username'] = username
            self.session['password'] = password

            return True

        except:
            print('no such user')

            return False

    def close(self):
        # TODO: remove any other attris in session
        self.session.pop('username', None)
