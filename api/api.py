import sqlite3
import datetime
import uuid

from flask import Flask, jsonify
from flask_restful import reqparse, abort, Api, Resource, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth

from packages import convert


# TODO: figure out a standardised way to process images. resolution, size etc.
# TODO: imp a way to add already uploaded images to already avaliable galleries
# TODO: look into building a basic color corrector/image manipulator on the
# frontend. JS?
# TODO: look into building 'gallery templates' for when a gallery is shared.
# TODO: IMP postgres
# TODO: IMP 'dev mode' disabling aws things, uploading localling instead.

# Config
# init app and db
app = Flask(__name__)
conn = sqlite3.connect('example.db')

# config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'
api = Api(app, '/gallery/v1')
db = SQLAlchemy(app)
auth = HTTPBasicAuth()

# database models
account_galleries = db.Table('account_galleries',
    db.Column('account_id', db.Integer, db.ForeignKey('account.id')),
    db.Column('gallery_id', db.Integer, db.ForeignKey('gallery.id'))
)

account_snaps = db.Table('account_snaps',
    db.Column('account_id', db.Integer, db.ForeignKey('account.id')),
    db.Column('snap_id', db.Integer, db.ForeignKey('snap.id'))
)

gallery_snaps = db.Table('gallery_snaps',
    db.Column('gallery_id', db.Integer, db.ForeignKey('gallery.id')),
    db.Column('snap_id', db.Integer, db.ForeignKey('snap.id'))
)


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    password = db.Column(db.String)
    initdate = db.Column(db.String, default=str(datetime.datetime.utcnow()))

    # relationships
    # comments
    galleries = db.relationship('Gallery', secondary=account_galleries,
        backref=db.backref('account', lazy='dynamic'))

    snaps = db.relationship('Snap', secondary=account_snaps,
        backref=db.backref('account', lazy='dynamic'))


    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return '<Account {}>'.format(self.id)


class Gallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    initdate = db.Column(db.String, default=str(datetime.datetime.utcnow()))
    private = db.Column(db.Boolean, default=True)
    shareuuid = db.Column(db.String, default='0')
    theme = db.Column(db.String, default='default')

    # relationship
    snaps = db.relationship('Snap', secondary=gallery_snaps,
        backref=db.backref('gallery', lazy='dynamic'))


    def __init__(self, title):
        self.title = title

    def __repr__(self):
        return '<Gallery {}>'.format(self.id)


class Snap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    initdate = db.Column(db.String, default=str(datetime.datetime.utcnow()))
    name = db.Column(db.String)
    private = db.Column(db.Boolean, default=True)


    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Snap {}>'.format(self.id)


db.create_all()


# helpers
def resp(status=None, data=None, link=None, error=None, message=None):
    """Function im using to build responses"""
    response = {
        'status': status, 'data': data, 'link': link,
        'error': error, 'message': message
    }

    remove_none = []

    for x in response:
        if response[x] == None:
            remove_none.append(x)

    for x in remove_none:
        del response[x]

    return response

# auth
# Basic HTTP auth
@auth.verify_password
def verify(username, password):
    get_account = Account.query.filter_by(username=username).first()

    if not Account.query.filter_by(username=username).first():
        return False

    else:
        if get_account.password == password:
            return True

        else:
            return False


# API resources
class Entry(Resource):
    @auth.login_required
    def get(self):
        entry = {
            'name': 'gallery api',
            'version': 'v1',
            'resources': ''
        }

        return entry, 200


class Shareuuid(Resource):
    def get(self, uuid):
        raw_gallery = Gallery.query.filter_by(shareuuid=uuid).first()

        if raw_gallery.private:
            response = resp(status='failed', error='this gallery is private')
            return response

        else:
            converted_to_json = convert.jsonify((raw_gallery,))[0]

            gallery = {
                'theme': converted_to_json['theme'],
                'snaps': converted_to_json['snaps']
            }

            response = resp(status='success', data=gallery)
            return response


class Accounts(Resource):
    @auth.login_required
    def get(self, id):
        raw_account = Account.query.filter_by(id=id).first()

        response = resp(status='success', data=convert.jsonify(raw_account))
        return response, 200


    @auth.login_required
    def put(self, id):
        parser = reqparse.RequestParser()
        parser.add_argument('galleries', type=str, help='help text')
        args = parser.parse_args()

        raw_account = Account.query.filter_by(id=id).first()

        if raw_account != None:
            if 'galleries' in args and args['galleries'] != None:
                raw_gallery = Gallery.query.filter_by(id=args['galleries']).first()

                if raw_gallery != None:
                    raw_account.galleries.append(raw_gallery)
                    db.session.commit()

                    response = resp(
                        status='success', link='/accounts/{}'.format(raw_account.id)
                        ), 201

                    return response

                else:
                    return resp(error='no such gallery id')

            else:
                return resp(error='must enter gallery id')

        else:
            return resp(error='no such account id')


    @auth.login_required
    def delete(self, id):
        raw_account = Account.query.filter_by(id=id).first()

        if auth.username() == raw_account.username:
            db.session.delete(raw_account)
            db.session.commit()

            response = resp(status='success', message='account successfully deleted')
            return response

        else:
            return resp(message='Account can only be if logged in as the same account.')


class AccountsL(Resource):
    @auth.login_required
    def get(self):
        raw_account = Account.query.filter_by(username=auth.username()).first()

        response = resp(data=convert.jsonify((raw_account,)), status='success')
        return response, 200


    def post(self):
        parser = reqparse.RequestParser()

        # accepted ARGs from api
        parser.add_argument('username', type=str, help='help text')
        parser.add_argument('password', type=str, help='help text')
        args = parser.parse_args()

        #process user input
        if args['username'] != None and args['password'] != None:
            new_account = Account(username=args['username'], password=args['password'])
            db.session.add(new_account)
            db.session.commit()

            response = resp(
                data=convert.jsonify((new_account,)),
                link='/accounts/{}'.format(new_account.id),
                status='success'
            )

            return response, 201

        else:
            response = resp(error='No post data', status='failed')
            return response, 400


class Galleries(Resource):
    def get(self, id):
        raw_gallery = Gallery.query.filter_by(id=id).first()

        if raw_gallery != None:

            response = resp(data=convert.jsonify((raw_gallery,)), status='success')
            return response, 200

        else:
            response = resp(status='failed', error='no such gallery id')
            return response, 400


    @auth.login_required
    def put(self, id):
        parser = reqparse.RequestParser()
        parser.add_argument('snaps', type=str, help='help text')
        parser.add_argument('private', type=str, help='help text')
        args = parser.parse_args()

        get_gallery = Gallery.query.filter_by(id=id).first()

        if get_gallery != None:
            if args['snaps']:
                raw_snap = Snap.query.filter_by(id=args['snaps']).first()
                if raw_snap != None:
                    get_gallery.snaps.append(raw_snap)
                    db.session.commit()
                    print('snaps is in there')

                else:
                    return resp(error='no such snap id')

            elif args['private']:
                if get_gallery.private:
                    get_gallery.private = False
                    db.session.commit()
                else:
                    get_gallery.private = True
                    db.session.commit()

            else:
                pass

        else:
            return resp(error='no such gallery id')


    @auth.login_required
    def delete(self, id):
        get_gallery = Gallery.query.filter_by(id=id).first()
        get_account = Account.query.filter_by(username=auth.username()).first()

        if get_gallery in get_account.galleries:
            db.session.delete(get_gallery)
            db.session.commit()

            response = resp(status='success', message='gallery successfully deleted')

            return response, 201

        else:
            return resp(message='gallery can only deleted by the account that posted it')


class GalleriesL(Resource):
    def get(self):
        accounts_galleries = Account.query.filter_by(username=auth.username()).first()
        if accounts_galleries:
            accounts_galleries = accounts_galleries.galleries

            response = resp(data=convert.jsonify(accounts_galleries), status='success')
            return response, 200

        else:
            response = resp(status='failed', error='Returned NoneType')
            return response, 401


    @auth.login_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('title', type=str, help='helper text')
        args = parser.parse_args()

        if args['title'] != None:
            raw_account = Account.query.filter_by(username=auth.username()).first()
            new_gallery = Gallery(title=args['title'])
            new_gallery.shareuuid = str(uuid.uuid4())

            new_gallery.account.append(raw_account)
            db.session.add(new_gallery)
            db.session.commit()

            response = resp(
                data=convert.jsonify((new_gallery,)),
                link='/galleries/{}'.format(new_gallery.id),
                status='success'
            )

            return response, 201

        else:
            response = resp(error='missing required data', message='')
            return response, 400


class Snaps(Resource):
    def get(self, id):
        raw_snap = Snap.query.filter_by(id=id).first()

        if raw_snap != None:
            response = resp(data=convert.jsonify((raw_snap,)), status='success')
            return response, 200

        else:
            response = resp(status='failed', error='no such snap id')
            return response, 400

    @auth.login_required
    def put(self, id):
        parser = reqparse.RequestParser()
        parser.add_argument('private', type=str, help='help text')
        args = parser.parse_args()

        get_snap = Snap.query.filter_by(id=id).first()

        if get_snap != None:
            if args['private']:
                if get_snap.private:
                    get_snap.private = False
                    db.session.commit()
                else:
                    get_snap.private = True
                    db.session.commit()

        else:
            return resp(error='no such snap id')

    @auth.login_required
    def delete(self, id):
        # TODO: delete physical file from s3 also

        get_account = Account.query.filter_by(username=auth.username()).first().snaps
        for snap in get_account:
            if snap.id == int(id):
                db.session.delete(snap)
                db.session.commit()

                response = resp(status='success', message='snap successfully deleted')

                return response, 201

        else:
            return resp(message='snap can only be deleted by the account that posted it')


class SnapsL(Resource):
    def get(self):
        accounts_snaps = Account.query.filter_by(username=auth.username()).first()
        if accounts_snaps:
            accounts_snaps = accounts_snaps.snaps

            response = resp(data=convert.jsonify(accounts_snaps), status='success')
            return response, 200

        else:
            response = resp(status='failed', error='Returned NoneType')
            return response, 401

    @auth.login_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, help='helper text')
        args = parser.parse_args()

        if args['name'] != None:
            raw_account = Account.query.filter_by(username=auth.username()).first()
            new_snap = Snap(name=args['name'])

            new_snap.account.append(raw_account)
            db.session.add(new_snap)
            db.session.commit()

            response = resp(
                data=convert.jsonify((new_snap,)),
                link='/snaps/{}'.format(new_snap.id),
                status='success'
            )

            return response, 201

        else:

            response = resp(error='missing required data', message='')
            return response, 400


# routes
api.add_resource(Entry, '/')
api.add_resource(Shareuuid, '/shareuuid/<uuid>')
api.add_resource(Accounts, '/accounts/<id>')
api.add_resource(AccountsL, '/accounts')
api.add_resource(Galleries, '/galleries/<id>')
api.add_resource(GalleriesL, '/galleries')
api.add_resource(Snaps, '/snaps/<id>')
api.add_resource(SnapsL, '/snaps')


if __name__ == '__main__':
    app.run(debug=True, port=5050)
