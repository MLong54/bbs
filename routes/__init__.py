import uuid, redis
from functools import wraps
from utils import log
from flask import session, request, abort

from models.user import User


def current_user():
    uid = session.get('user_id', '')
    u = User.one(id=uid)
    return u


def user_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        u = current_user()
        if u :
            return f(*args, **kwargs)
        else:
            abort(401)

    return wrapper


csrf_tokens = 'csrf_token'
re = redis.Redis(host='localhost', port=6379, db=0)


def csrf_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.args['token']
        log('token:', token)
        u = current_user()
        if re.hexists(csrf_tokens, token):
            re.hdel(csrf_tokens, token)
            return f(*args, **kwargs)
        else:
            abort(401)

    return wrapper


def new_csrf_token():
    u = current_user()
    token = str(uuid.uuid4())
    re.hset(csrf_tokens, token, token)
    return token
