def something_session_related():
    pass

class SessionHandler():
    def __init__(self, session, username, password):
        self.session = session
        self.username = username
        self.password = password

    def new(self):
        self.session['username'] = username
        # TODO: password should get check in db only.

        return self.session

    def close(self):
        session.pop('username', None)


    def _print_session(self):
        print(self.session)
