import requests

from config import config


class SessionHandler():
    def __init__(self, session):
        self.session = session

    def new(self, username, password):
        self.session['username'] = username
        # TODO: password should get check in db only.
        # r = requests.post(f'{BASEURL}/accounts?username={username}&password={password}')

        if session['username']:
            # if username in database
            # check password
            # error check
            # return session
            # else add new user and password to database
            pass

        return self.session

    def close(self):
        # TODO: remove any other attris in session
        self.session.pop('username', None)
