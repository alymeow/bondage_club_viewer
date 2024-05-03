import hashlib

import re
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime, timedelta
import simplejson as json
import pytz
from utils import renderer

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///logs.db'
app.config['LOG_LIMIT'] = 20

db = SQLAlchemy(app)

userdb = {}
conf_use_renderer = True
conf_show_room = True
conf_show_sender_id = True
conf_show_session = True
conf_show_sender_name = True
dt_format = "%Y-%m-%dT%H:%M:%S.%fZ"
dp_format = "%m/%d %H:%M"
localzone = pytz.timezone('Asia/Shanghai')


class Logs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    json = db.Column(db.Text, nullable=False)
    sender = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text)
    chat_room = db.Column(db.Text)
    session = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.Text, nullable=False)
    type = db.Column(db.Text, nullable=False)
    hash = db.Column(db.Text, unique=True)
    target = db.Column(db.Text)

    def __repr__(self):
        return '<Logs %r>' % self.json

    def __str__(self):
        return '<Logs %r>' % self.json

    def to_dict(self):
        data=json.loads(self.json)
        data['log_id'] = self.id
        return data

    def to_conversion(self):
        dt_obj = datetime.strptime(self.timestamp, dt_format).replace(tzinfo=pytz.UTC).astimezone(localzone)
        sender = get_user_by_id(self.sender)
        ret = {"timestamp": dt_obj.strftime(dp_format), "color": sender['color'], 'name': sender['name'],
               'id': sender['id'], 'session': self.session, 'msg_style': None}

        if self.type == 'Chat':
            ret['message'] = self.content
        elif self.type == 'Whisper':
            ret['msg_style'] = 'font-weight: bold'
            ret['message'] = "悄悄话：{}".format(self.content)
        elif self.type == 'Emote':
            ret['msg_style'] = 'color: #AAA'
            ret['message'] = "*{}".format(self.content)
        elif self.type == 'Activity':
            ret['msg_style'] = 'color: #AAA'
            if conf_use_renderer:
                try:
                    msg = renderer.element_renderer_activity(json.loads(self.json))
                    ret['message'] = msg if msg is not None else "({})".format(self.content)
                except:
                    ret['message'] = "({})".format(self.content)
            else:
                ret['message'] = "({})".format(self.content)

        elif self.type == 'Action':
            ret['msg_style'] = 'color: #AAA'
            if conf_use_renderer:
                try:
                    msg = renderer.element_renderer_action(json.loads(self.json))
                    ret['message'] = msg if msg is not None else "({})".format(self.content)
                except:
                    ret['message'] = "*{}".format(self.content)
            else:
                ret['message'] = "*{}".format(self.content)
        else:
            ret['message'] = "{} #{}".format(self.content, self.type)

        return ret


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=False, nullable=False)
    color = db.Column(db.String(10), unique=False, nullable=False)

    def __repr__(self):
        return "<User {}, {}>".format(self.name, self.color)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            # 'url': '/id/{}'.format(self.id)
        }


def get_user_by_id(id, reload=False):
    id = int(id)
    if reload or id not in userdb.keys():
        user = Users.query.get_or_404(id)
        userdb[id] = user.to_dict()
    return userdb.get(id)


def make_response(status=200, data=None, message=""):
    return {"status": status, "message": message, 'data': data}


@app.route('/')
def index():
    return 'bcv'


@app.route('/users', methods=['GET', 'POST'])
def get_users():
    users = Users.query.all()
    return jsonify([user.to_dict() for user in users])


@app.route('/user/<name>', methods=['GET'])
@app.route('/u/<name>', methods=['GET'])
def get_user(name):
    if request.args.get('name') is not None:
        user = Users.query.filter(Users.name.ilike(name)).all()
        data = [user.to_dict() for user in user]
        return render_template("id.html", table_data=data)

    try:
        data = [get_user_by_id(int(name))]
        return render_template("id.html", table_data=data)

    except:
        user = Users.query.filter(Users.name.ilike(name)).all()
        data = [user.to_dict() for user in user]
        return render_template("id.html", table_data=data)


@app.route('/id/{int:id}/set', methods=['GET'])
def set_user():
    color = request.args.get('color')
    if color is not None:
        user = Users.query.get(id)
        print(user['color'], color)
        return jsonify(user.to_dict())
    else:
        return jsonify('ok')


@app.route('/id/<int:id>', methods=['GET'])
@app.route('/sender/<int:id>', methods=['GET'])
def get_logs_sender(id):
    if request.args.get("set_color") is not None:
        color = request.args.get("set_color")
        user = Users.query.get(id)

        if len(color) != 3 and len(color) != 6:
            return jsonify(make_response(status=400, data=user.color, message="#{} is not a valid color".format(color)))

        if not check_color_str(color):
            return jsonify(make_response(status=400, data=user.color, message="#{} is not a valid color".format(color)))

        color = "#{}".format(color)
        print("set user {} color: {} -> {}".format(user.id, user.color, color))

        try:
            user.color = color
            db.session.commit()
            user = get_user_by_id(id, reload=True)
            return jsonify(make_response(status=200, data=user['color']))

        except:
            db.session.rollback()
            return jsonify(make_response(status=400, data=get_user_by_id(id)['color']))

    limit = request.args.get('limit')
    app.config['LOG_LIMIT'] = int(limit) if limit is not None else app.config['LOG_LIMIT']

    page = 1 if request.args.get('page') is None else int(request.args.get('page'))
    page = 1 if page < 1 else page
    offset = (int(page) - 1) * app.config['LOG_LIMIT']

    logs = Logs.query.filter(Logs.sender == id).order_by(Logs.timestamp).limit(app.config['LOG_LIMIT']).offset(
        offset).all()
    if request.args.get('raw') is None:
        return render_template("records.html", table_data=[log.to_conversion() for log in logs],
                               url='/id/{}?page={}'.format(id, page + 1), title="搜索结果：User {}".format(id))
    else:
        return jsonify([log.to_dict() for log in logs])


@app.route('/id/<int:id>/session', methods=['GET'])
@app.route('/sender/<int:id>/session', methods=['GET'])
def get_logs_sender_sessions(id):
    logs = Logs.query.filter(Logs.sender == id).order_by(Logs.timestamp).all()
    sess = []
    ret = []
    user = get_user_by_id(id)
    for log in logs:
        if log.session not in sess:
            sess.append(log.session)
            ret.append({"timestamp": log.timestamp, "session": log.session, 'url': "/s/{}".format(log.session)})
    return render_template('sessions.html', table_data=ret, id=id, name=user['name'], color=user['color'])


@app.route('/timestamp/<string:ts>', methods=['GET'])
@app.route('/t/<string:ts>', methods=['GET'])
def get_logs_timestamp(ts):
    limit = request.args.get('limit')
    app.config['LOG_LIMIT'] = int(limit) if limit is not None else app.config['LOG_LIMIT']

    page = 1 if request.args.get('page') is None else int(request.args.get('page'))
    page = 1 if page < 1 else page
    offset = (int(page) - 1) * app.config['LOG_LIMIT']

    try:
        datetime.strptime(ts, dt_format)
        str_t = ts
    except ValueError:
        d1 = 2023
        d2 = 1
        d3 = 1
        t1 = 1
        t2 = 1
        ddata = ts.split("-")
        if len(ddata) > 0:
            d1 = int(ddata[0])
        if len(ddata) > 1:
            d2 = int(ddata[1])
        if len(ddata) > 2:
            d3 = int(ddata[2])
        if len(ddata) > 3:
            t1 = int(ddata[3])
        if len(ddata) > 4:
            t2 = int(ddata[4])

        str_t = datetime(year=d1, month=d2, day=d3, hour=t1, minute=t2, second=0).strftime(dt_format)

    logs = Logs.query.order_by(Logs.timestamp).filter(Logs.timestamp >= str_t).offset(offset).limit(
        app.config['LOG_LIMIT']).all()

    if request.args.get('raw') is None:
        return render_template("records.html", table_data=[log.to_conversion() for log in logs],
                               url='{}?page={}'.format(request.base_url, page + 1), title="自 {} 后的消息".format(str_t))
    else:
        return jsonify([log.to_dict() for log in logs])


@app.route('/session/<string:session>', methods=['GET'])
@app.route('/s/<string:session>', methods=['GET'])
def get_logs_session(session):
    logs = Logs.query.filter(Logs.session == session).order_by(Logs.timestamp).all()

    if request.args.get('raw') is not None:
        return jsonify([log.to_dict() for log in logs])
    elif request.args.get('del') is not None:
        if request.args.get('del') == '1':
            print("remove session: {}".format(session))
            count = 0
            for log in logs:
                count += 1
                db.session.delete(log)
            db.session.commit()
            if count > 1:
                return jsonify({"deleted": session, 'records count': count})
            else:
                return jsonify({"msg": 'record is empty'})
        else:
            return render_template('confirm.html', session_id=session, url="/s/{}?del=1".format(session))

    else:
        return render_template('dialog.html', table_data=[log.to_conversion() for log in logs], session_id=session)


@app.route('/search/<string:search>', methods=['GET'])
@app.route('/q/<string:search>', methods=['GET'])
def get_logs_search(search):
    limit = request.args.get('limit')
    app.config['LOG_LIMIT'] = int(limit) if limit is not None else app.config['LOG_LIMIT']

    page = 1 if request.args.get('page') is None else int(request.args.get('page'))
    page = 1 if page < 1 else page
    offset = (int(page) - 1) * app.config['LOG_LIMIT']

    logs = Logs.query.order_by(Logs.timestamp)
    if request.args.get('force') is None:
        logs = logs.filter(Logs.content.like(search)).offset(offset).limit(
            app.config['LOG_LIMIT']).all()
    else:
        logs = logs.filter_by(content=search).offset(offset).limit(
            app.config['LOG_LIMIT']).all()

    if request.args.get('raw') is None:
        return render_template("records.html", table_data=[log.to_conversion() for log in logs],
                               url='{}?page={}'.format(request.base_url, page + 1), title="搜索结果：{}".format(search))
    else:
        return jsonify([log.to_conversion() for log in logs])


@app.route('/dedup/<int:start_id>', methods=['GET'])
def get_logs_dedup(start_id):
    log_id = start_id
    count = request.args.get('p')
    count = 1 if count is None else int(count)
    remove_cound = 0
    page = 1000
    count *= page
    while log_id < start_id + count:
        print("start from {}".format(log_id))
        logs = Logs.query.filter(Logs.id>=log_id).limit(page).all()
        log_id += page
        final_id = -1

        while len(logs) > 1:
            log0 = logs[0]
            log1 = logs[1]
            logs = logs[1:]
            final_id = log1.id

            if log0.content == log1.content and log0.sender == log1.sender:
                delta_d = datetime.strptime(log1.timestamp, dt_format) - datetime.strptime(log0.timestamp, dt_format)
                delta_t = timedelta(milliseconds=1000)
                if delta_t < delta_d:
                    continue

                j0 = json.loads(log0.json)
                j1 = json.loads(log1.json)
                del j0['timestamp']
                del j1['timestamp']

                hash0 = hashlib.md5(json.dumps(j0, sort_keys=True).encode('utf-8')).hexdigest()
                hash1 = hashlib.md5(json.dumps(j1, sort_keys=True).encode('utf-8')).hexdigest()

                if hash0 == hash1:
                    print("remove same record: x{} {}".format(log0.id, log1.id))
                    remove_cound += 1
                    db.session.delete(log0)

        db.session.commit()
    return jsonify({"msg": "finished", "remove_count": remove_cound, "last_id": final_id})


def check_color_str(color):
    import re
    rex = re.compile(r'^[A-Fa-f0-9]*$')
    return bool(rex.match(color))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
