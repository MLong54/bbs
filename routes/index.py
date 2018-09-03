import os, sys
import uuid

from flask import (
    render_template,
    request,
    redirect,
    session,
    url_for,
    Blueprint,
    make_response,
    abort,
    send_from_directory
)
from werkzeug.utils import secure_filename

from models.reply import Reply
from models.topic import Topic
from models.user import User
from routes import current_user

import json

import redis

cache = redis.StrictRedis()

from utils import log

main = Blueprint('index', __name__)

"""
用户在这里可以
    访问首页
    注册
    登录

用户登录后, 会写入 session, 并且定向到 /profile
"""


@main.route("/")
def index():
    u = current_user()
    return redirect(url_for('topic.index'))


@main.route("/register", methods=['GET', 'POST'])
def register():
    m = request.method
    if 'GET' == m:
        return render_template("register.html")
    elif 'POST' == m:
        form = request.form.to_dict()
        # 用类函数来判断
        u = User.register(form)
        return redirect(url_for('.login'))


@main.route("/login", methods=['GET', 'POST'])
def login():
    m = request.method
    if 'GET' == m:
        return render_template('login.html')
    elif 'POST' == m:
        form = request.form
        u = User.validate_login(form)
        if u is None:
            return redirect(url_for('.index'))
        else:
            # session 中写入 user_id
            session['user_id'] = u.id
            # 设置 cookie 有效期为 永久
            session.permanent = True
            # 转到 topic.index 页面
            return redirect(url_for('topic.index'))


@main.route("/api")
def api():
    return render_template("api.html")


@main.route("/about")
def about():
    return render_template("abort.html")


def created_topic(user_id):
    # O(n)
    # ts = Topic.all(user_id=user_id)

    k = 'created_topic_{}'.format(user_id)
    if cache.exists(k):
        v = cache.get(k)
        ts = json.loads(v)
        return ts
    else:
        ts = Topic.all(user_id=user_id)
        v = json.dumps([t.json() for t in ts])
        cache.set(k, v)
        return ts


def replied_topic(user_id):
    # O(m*n)
    # rs = Reply.all(user_id=user_id)
    # ts = []
    # for r in rs:
    #     t = Topic.one(id=r.topic_id)
    #     ts.append(t)
    # return ts

    k = 'replied_topic_{}'.format(user_id)
    if cache.exists(k):
        v = cache.get(k)
        ts = json.loads(v)
        return ts
    else:
        rs = Reply.all(user_id=user_id)
        ts = []
        for r in rs:
            t = Topic.one(id=r.topic_id)
            ts.append(t)

        v = json.dumps([t.json() for t in ts])
        cache.set(k, v)

        return ts


@main.route('/profile')
def profile():
    u = current_user()
    if u is None:
        return redirect(url_for('topic.index'))
    else:
        return render_template('profile.html', user=u)


@main.route('/user/<int:id>')
def user_detail(id):
    u = User.one(id=id)
    if u is None:
        abort(404)
    else:
        return render_template('profile.html', user=u)


@main.route('/image/add', methods=['POST'])
def avatar_add():
    file = request.files['avatar']

    # ../../root/.ssh/authorized_keys
    # filename = secure_filename(file.filename)
    suffix = file.filename.split('.')[-1]
    file.filename = '{}.{}'.format(str(uuid.uuid4()), suffix)
    #因为相对路径不能用，所以暂时使用绝对路径
    path = os.path.join(sys.path[0] + '/images', file.filename)
    # path = os.path.join('images/', file.filename)

    print('save fuck images  filename:<{}> , path:<{}>'.format(file.filename, path))
    file.save(path)

    u = current_user()
    User.update(u.id, image='/images/{}'.format(file.filename))

    return redirect(url_for('.setting'))


@main.route('/images/<filename>')
def image(filename):
    # 不要直接拼接路由，不安全，比如
    # open(os.path.join('images', filename), 'rb').read()
    return send_from_directory('images', filename)


@main.route('/setting', methods=['POST', 'GET'])
def setting():
    u = current_user()

    return render_template('setting.html', u=u)


@main.route('/setting/update_user', methods=['POST'])
def update_user():
    u = current_user()
    form:dict = request.form.to_dict()

    old_pass = form.get('old_pass', None)
    if old_pass is not None and User.salted_password(old_pass) != u.password:
        print('原始密码不对')
        return render_template('setting.html', u=u)
    elif old_pass is not None and User.salted_password(old_pass) == u.password:
        form['password'] = User.salted_password(form['new_pass'])

    print('setting form <{}>'.format(form))
    u = User.update(u.id, **form)
    print('update u {}'.format(u))
    return redirect(url_for('.setting'))


@main.route('/user/<name>')
def userinfo(name):
    u = User.one(username=name)
    #找到自己创建的topic
    ts = Topic.all(user_id=u.id)

    #参与过的
    rs = Reply.all(user_id=u.id)
    tes = []
    for r in rs:
        tes.append(Topic.one(id=r.topic_id))

    return render_template('userinfo.html', ts=ts, tes=tes, user=u)
