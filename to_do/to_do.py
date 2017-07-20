import os
import sqlite3
from flask import Flask, request, redirect, url_for, Response, g
from flask import current_app, session
import json
from copy import deepcopy
import time
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config.from_object(__name__)  # loading config from this same file, to_do.py
# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'to_do.db'),
))
app.config.from_envvar('TODO_SETTINGS', silent=True)

def get_db():
    """Opens a new db connection is if its not present in the current
    application context"""
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def connect_db():
    """connects to the specific database"""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


@app.route('/get_current_username', methods=['GET'])
def get_current_username():
    response = {}
    response['username'] = session['username']
    return Response(json.dumps(response), mimetype='application/json')


@app.route('/sync', methods=['GET'])
def show_entries():
    cur = get_db().execute('select task_id, task_name, is_done from task where task_creator = ? order by task_id asc',[session['username']])
    entries = cur.fetchall()
    json_array = []
    for entry in entries:
        json_array.append([x for x in entry])
    return Response(json.dumps(json_array), mimetype='json/application')

@app.route('/assigned_to', methods=['GET'])
def tasks_assigned_to():
    cur = get_db().execute('select task_id, task_name, is_done from task where task_id in (select task_id from assignment where assignee_id = ?) order by task_id asc',[get_user_id(session['username'])])
    entries = cur.fetchall()
    json_array = []
    for entry in entries:
        json_array.append([x for x in entry])
    return Response(json.dumps(json_array), mimetype='json/application')

@app.route('/add', methods=['POST'])
def add_entry():
    db = get_db()
    db.execute('insert into task (task_name, is_done, task_creator) values (?, ?, ?)', [request.json[0], request.json[1], session['username']])
    db.commit()
    return redirect(url_for('show_entries'))


@app.route('/done', methods=['POST'])
def update_status():
    db = get_db()
    is_done = request.json[1]
    task_id = request.json[0]
    is_done = 1 - is_done
    db.execute('update task set is_done = ? where task_id=?', [is_done, task_id])
    db.commit()
    created_tasks = json.loads(show_entries().data.decode("utf-8"))
    assigned_tasks = json.loads(tasks_assigned_to().data.decode("utf-8"))
    to_return = {'created_tasks': created_tasks, 'assigned_tasks': assigned_tasks}
    return Response(json.dumps(to_return), mimetype='json/application')


@app.route('/delete', methods = ['POST'])
def delete_task():
    task_id = request.json
    db = get_db()
    db.execute('delete from task where task_id = ?', [task_id])
    db.commit()
    return show_entries()


@app.route('/assign', methods=['POST'])
def assign_task():
    task_id = request.json[0]
    assignee = request.json[1]
    assignee_id = get_user_id(assignee)
    if assignee_id is None:
        return Response(json.dumps({'alert': 'User name doesn\'t exists'}))
    assigner_id = get_user_id(session['username'])
    db = get_db()
    if assignee_id is not None:
        db.execute('insert into assignment values (NULL, ?, ?, ?)', [task_id, assigner_id, assignee_id])
        db.commit()
    return Response(json.dumps({'alert': 'save successful'}))


@app.route('/task')
def to_do():
    return current_app.send_static_file('using_js.html')


@app.route('/')
def index():
    if 'username' in session:
        return 'Logged in as %s' % session['username']
    return 'You are not logged in'

@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    if request.method == 'POST':
        db = get_db()
        hashed_password = generate_password_hash(request.form['password'])
        db.execute('insert into user values (NULL, ?, ?)', [request.form['username'], hashed_password])
        db.commit()

        return 'Signup successful'

    return ''' <form method="post">
            <p><input type=text name=username>
            <p><input type=password name=password>
            <p><input type=submit value=Login>
        </form>
    '''


def check_credentials(username, password):
    db = get_db()
    cur = db.execute('select user_password from user where user_name = ?', [username])
    return check_password_hash(cur.fetchone()[0], password)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if check_credentials(request.form['username'], request.form['password']):
            session['username'] = request.form['username']
            return redirect(url_for('to_do'))

        return 'Invalid Credentials or Username doesn\' exits'

    return ''' <form method="post">
            <p><input type=text name=username>
            <p><input type=password name=password>
            <p><input type=submit value=Login>
        </form>
    '''


@app.route('/logout')
def logout():
    session.pop('username', None)
    return 'Logout Successful'

app.secret_key = 'my secret key'


def get_user_id(username):
    db = get_db()
    cur = db.execute('select user_id from user where user_name = ?', [username])
    row_obj = cur.fetchone()

    if row_obj is None:
        return None
    return row_obj[0]


def get_username_by_id(user_id):
    db = get_db()
    cur = db.execute('select user_name from user where user_id = ?', [user_id])
    row_obj = cur.fetchone()

    if row_obj is None:
        return None
    return row_obj[0]


@app.route('/chat/sync', methods=['POST'])
def chat():
#    if request.json['recent_message_id'] == 0:
#        return get_all_messages_using_task_id(request.json['task_id'])
    latest_message_id_from_db = 0
    while True:
        time.sleep(0.5)
        db = get_db()
        cur = db.execute('select message_id from message where task_id = ? order by message_id desc limit 1',[request.json['task_id']])
        db_row = cur.fetchone()
        if db_row is not None:
            latest_message_id_from_db = db_row[0]

        if latest_message_id_from_db > request.json['recent_message_id']:
            return get_all_messages_using_task_id(request.json['task_id'])


def get_all_messages_using_task_id(task_id):
    db = get_db()
    cur = db.execute('select message_id, task_id, message_text, sender_id from message where task_id = ? order by message_id asc',[task_id])
    entries = cur.fetchall()
    json_dict = {}
    json_array = []
    for entry in entries:
        for key, value in zip(['message_id', 'task_id', 'message_text', 'sender_name'], entry):
            if(key == 'sender_name'):
                value = get_username_by_id(value)
            json_dict[key] = value
        json_array.append(deepcopy(json_dict))
    return Response(json.dumps(json_array), mimetype='json/application')


@app.route('/chat')
def chat_main():
    return current_app.send_static_file('chat.html')


@app.route('/chat/save_chat', methods=['POST'])
def save_chat():
    task_id = request.json['task_id']
    message_text = request.json['message_text']
    sender_id = get_user_id(session['username'])
    db = get_db()
    db.execute('insert into message values (NULL, ?, ?, ?)', [task_id, message_text, sender_id])
    db.commit()
    return Response("Saved")

if __name__ == "__main__":
    app.run(port=7000, threaded=True)

