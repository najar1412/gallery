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
# TODO: build something that checks images on s3 with database snaps, returning
# any mismatches. app side?

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

account_batches = db.Table('account_batches',
    db.Column('account_id', db.Integer, db.ForeignKey('account.id')),
    db.Column('batch_id', db.Integer, db.ForeignKey('batch.id'))
)

account_snaps = db.Table('account_snaps',
    db.Column('account_id', db.Integer, db.ForeignKey('account.id')),
    db.Column('snap_id', db.Integer, db.ForeignKey('snap.id'))
)

batch_snaps = db.Table('batch_snaps',
    db.Column('batch_id', db.Integer, db.ForeignKey('batch.id')),
    db.Column('snap_id', db.Integer, db.ForeignKey('snap.id'))
)

batch_galleries = db.Table('batch_galleries',
    db.Column('batch_id', db.Integer, db.ForeignKey('batch.id')),
    db.Column('gallery_id', db.Integer, db.ForeignKey('gallery.id'))
)

gallery_snaps = db.Table('gallery_snaps',
    db.Column('gallery_id', db.Integer, db.ForeignKey('gallery.id')),
    db.Column('snap_id', db.Integer, db.ForeignKey('snap.id'))
)

theme_gallery = db.Table('theme_gallery',
    db.Column('theme_id', db.Integer, db.ForeignKey('theme.id')),
    db.Column('gallery_id', db.Integer, db.ForeignKey('gallery.id'))
)


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    password = db.Column(db.String)
    initdate = db.Column(db.String, default=str(datetime.datetime.utcnow()))

    # relationships
    # comments
    batches = db.relationship('Batch', secondary=account_batches,
        backref=db.backref('account', lazy='dynamic'))

    galleries = db.relationship('Gallery', secondary=account_galleries,
        backref=db.backref('account', lazy='dynamic'))

    snaps = db.relationship('Snap', secondary=account_snaps,
        backref=db.backref('account', lazy='dynamic'))


    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return '<Account {}>'.format(self.id)


class Batch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    initdate = db.Column(db.String, default=str(datetime.datetime.utcnow()))

    # relationship
    snaps = db.relationship('Snap', secondary=batch_snaps,
        backref=db.backref('batch', lazy='dynamic'))

    galleries = db.relationship('Gallery', secondary=batch_galleries,
        backref=db.backref('batch', lazy='dynamic'))


    def __init__(self, title):
        self.title = title

    def __repr__(self):
        return '<Batch {}>'.format(self.id)


class Gallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    initdate = db.Column(db.String, default=str(datetime.datetime.utcnow()))
    private = db.Column(db.Boolean, default=True)
    shareuuid = db.Column(db.String, default='0')

    # relationship
    snaps = db.relationship('Snap', secondary=gallery_snaps,
        backref=db.backref('gallery', lazy='dynamic'))
    # TODO: Theme should be one to many
    theme = db.relationship('Theme', secondary=theme_gallery,
        backref=db.backref('gallery', lazy='dynamic'))


    def __init__(self, title):
        self.title = title

    def __repr__(self):
        return '<Gallery {}>'.format(self.id)


class Snap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    initdate = db.Column(db.String, default=str(datetime.datetime.utcnow()))
    name = db.Column(db.String)
    snap_original = db.Column(db.String)
    snap_lores = db.Column(db.String)
    snap_thumb = db.Column(db.String)
    private = db.Column(db.Boolean, default=True)


    def __init__(self, name, snap_original, snap_lores, snap_thumb):
        self.name = name
        self.snap_original = snap_original
        self.snap_lores = snap_lores
        self.snap_thumb = snap_thumb

    def __repr__(self):
        return '<Snap {}>'.format(self.id)


class Theme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    initdate = db.Column(db.String, default=str(datetime.datetime.utcnow()))
    name = db.Column(db.String)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Theme {}>'.format(self.name)


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


class Batches(Resource):
    def get(self, id):
        raw_batch = Batch.query.filter_by(id=id).first()

        if raw_batch != None:
            # batch[0]['snaps] returns instrumentedlist and wont give access to
            # relationships in the model. Find a fix. Until then Overwritting 'snaps'
            # key with a request to Snap model.
            # Same as above but with galleries.
            batch = convert.jsonify((raw_batch,))

            batch_snaps = batch[0]['snaps']
            snaps = []
            galleries = []
            for snap in batch_snaps:
                raw_snap = Snap.query.filter_by(id=snap['id']).first()
                json_snap = convert.jsonify((raw_snap,))[0]
                snaps.append(json_snap)
                for gallery in json_snap['gallery']:
                    raw_gallery = Gallery.query.filter_by(id=gallery['id']).first()
                    json_gallery = convert.jsonify((raw_gallery,))[0]
                    if json_gallery not in galleries:
                        galleries.append(json_gallery)
                    

            # overrite snaps in batch
            batch[0]['snaps'] = snaps
            batch[0]['galleries'] = galleries

            response = resp(data=batch, status='success')
            return response, 200

        else:
            response = resp(status='failed', error='no such gallery id')
            return response, 400


    @auth.login_required
    def put(self, id):
        parser = reqparse.RequestParser()
        parser.add_argument('snaps', type=str, help='help text')
        parser.add_argument('galleries', type=str, help='help text')
        args = parser.parse_args()

        get_batch = Batch.query.filter_by(id=id).first()

        if get_batch != None:
            if args['snaps']:
                raw_snap = Snap.query.filter_by(id=args['snaps']).first()
                if raw_snap != None:
                    get_batch.snaps.append(raw_snap)
                    db.session.commit()
                    print('snaps is in there')

                else:
                    return resp(error='no such snap id')

            if args['galleries']:
                raw_gallery = Gallery.query.filter_by(id=args['galleries']).first()
                if raw_gallery != None:
                    get_batch.galleries.append(raw_gallery)
                    db.session.commit()
                    print('snaps is in there')

                else:
                    return resp(error='no such snap id')

            else:
                pass

        else:
            return resp(error='no such gallery id')


    @auth.login_required
    def delete(self, id):
        get_batch = Batch.query.filter_by(id=id).first()
        get_account = Account.query.filter_by(username=auth.username()).first()

        if get_batch in get_account.batches:
            db.session.delete(get_batch)
            db.session.commit()

            response = resp(status='success', message='batch successfully deleted')

            return response, 201

        else:
            return resp(message='batch can only deleted by the account that posted it')


class BatchesL(Resource):
    def get(self):
        accounts_galleries = Account.query.filter_by(username=auth.username()).first()
        if accounts_galleries:
            accounts_batches = accounts_galleries.batches

            response = resp(data=convert.jsonify(accounts_batches), status='success')
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

            new_batch = Batch(title=args['title'])
            new_batch.account.append(raw_account)

            db.session.add(new_batch)
            db.session.commit()

            response = resp(
                data=convert.jsonify((new_batch,)),
                link='/batches/{}'.format(new_batch.id),
                status='success'
            )

            return response, 201

        else:
            response = resp(error='missing required data', message='')
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
        parser.add_argument('theme', type=str, help='help text')
        args = parser.parse_args()

        get_gallery = Gallery.query.filter_by(id=id).first()

        if get_gallery != None:
            if args['snaps']:
                list_of_snaps = args['snaps'].split(' ')
                for snap in list_of_snaps:
                    raw_snap = Snap.query.filter_by(id=snap).first()
                    if raw_snap != None:
                        get_gallery.snaps.append(raw_snap)
                        db.session.commit()
                        print('snaps is in there')

            if args['private']:
                if get_gallery.private:
                    get_gallery.private = False
                    db.session.commit()
                else:
                    get_gallery.private = True
                    db.session.commit()

            if args['theme']:
                get_theme = Theme.query.filter_by(name=args['theme']).first()
                if get_theme:
                    get_gallery.theme.remove(get_gallery.theme[0])
                    get_gallery.theme.append(get_theme)
                    db.session.commit()

                    return resp(message='Theme has been changed.')


                else:
                    print('No such theme id')
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
        parser.add_argument('snaps', type=str, help='helper text')
        args = parser.parse_args()

        if args['title'] != None:
            raw_account = Account.query.filter_by(username=auth.username()).first()
            default_theme = Theme.query.filter_by(name='default').first()

            new_gallery = Gallery(title=args['title'])
            new_gallery.shareuuid = str(uuid.uuid4())
            new_gallery.theme.append(default_theme)
            new_gallery.account.append(raw_account)

            if args['snaps'] != '':
                snap_list = args['snaps'].split(' ')
                for snap_id in snap_list:
                    raw_snap = Snap.query.filter_by(id=snap_id).first()
                    new_gallery.snaps.append(raw_snap)

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
        # TODO: IMP - snap_original, snap_lores, snap_thumb
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, help='helper text')
        parser.add_argument('snap_original', type=str, help='helper text')
        parser.add_argument('snap_lores', type=str, help='helper text')
        parser.add_argument('snap_thumb', type=str, help='helper text')
        args = parser.parse_args()

        if args['name'] != None:
            raw_account = Account.query.filter_by(username=auth.username()).first()
            new_snap = Snap(name=args['name'], snap_original=args['name'], snap_lores=args['name'], snap_thumb=args['name'])

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


class Themes(Resource):
    def get(self, id):
        raw_theme = Theme.query.filter_by(id=id).first()

        if raw_theme != None:
            response = resp(data=convert.jsonify((raw_theme,)), status='success')
            return response, 200

        else:
            response = resp(status='failed', error='no such snap id')
            return response, 400

    def put(self, id):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, help='help text')
        args = parser.parse_args()

        get_theme = Theme.query.filter_by(id=id).first()

        if get_theme != None:
            if args['name']:
                if get_theme.name:
                    get_theme.name = args['name']
                    db.session.commit()

                    return resp(status='success', message='theme has been renamed')

        else:
            return resp(error='no such theme id')

    def delete(self, id):
        # TODO: delete physical file from s3 also

        get_theme = Theme.query.filter_by(id=id).first()
        if get_theme:
            db.session.delete(get_theme)
            db.session.commit()

            response = resp(status='success', message='theme successfully deleted')

            return response, 201

        else:
            return resp(message='theme id does not exist')


class ThemesL(Resource):
    def get(self):
        get_theme = Theme.query.all()
        if get_theme:

            response = resp(data=convert.jsonify(get_theme), status='success')
            return response, 200

        else:
            response = resp(status='failed', error='Returned NoneType')
            return response, 401

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, help='helper text')
        args = parser.parse_args()

        if args['name'] != None:
            new_theme = Theme(name=args['name'])

            db.session.add(new_theme)
            db.session.commit()

            response = resp(
                data=convert.jsonify((new_theme,)),
                link='/themes/{}'.format(new_theme.id),
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
api.add_resource(Batches, '/batches/<id>')
api.add_resource(BatchesL, '/batches')
api.add_resource(Snaps, '/snaps/<id>')
api.add_resource(SnapsL, '/snaps')
api.add_resource(Themes, '/themes/<id>')
api.add_resource(ThemesL, '/themes')


if __name__ == '__main__':
    app.run(debug=True, port=5050)
