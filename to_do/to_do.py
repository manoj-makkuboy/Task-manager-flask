import os
import sqlite3
from flask import Flask, request, redirect, url_for, flash, Response, g
from flask import current_app, session
import json
from copy import deepcopy

app = Flask(__name__)
app.config.from_object(__name__)  # loading config from this same file, to_do.py

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'to_do.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
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


def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """ Initializes the database."""
    init_db()
    print('Initialized the database.')


@app.route('/sync', methods=['GET'])
def show_entries():
    db = get_db()
    cur = db.execute('select task_id, task_name, is_done from task where task_creator = ? order by task_id asc',[session['username']])
    entries = cur.fetchall()
    json_array = []
    for entry in entries:
        json_array.append([x for x in entry])
    json_array.append(session['username'])
    return Response(json.dumps(json_array), mimetype='json/application')


@app.route('/add', methods=['POST'])
def add_entry():
    recievedJSON = request.json
    db = get_db()
    db.execute('insert into task (task_name, is_done, task_creator) values (?, ?, ?)', [recievedJSON[0], recievedJSON[1], session['username']])
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))


@app.route('/done', methods=['POST'])
def update_status():
    recievedJSON = request.json
    db = get_db()

    is_done = recievedJSON[1]
    task_id = recievedJSON[0]

    is_done = 1 - is_done

    db.execute('update task set is_done = ? where task_id=?', [is_done, task_id])

    db.commit()
    flash('update successful')
    return show_entries()   # sends Response() the entire JSON from serverside


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
    assigner_id = get_user_id(session['username'])
    db = get_db()
    if assignee_id != None:
        db.execute('insert into assignment values (NULL, ?, ?, ?)', [task_id, assigner_id, assignee_id])
        db.commit()
    return show_entries()


@app.route('/task')
def to_do():
    return current_app.send_static_file('using_js.html')


@app.route('/')
def index():
    if 'username' in session:
        return 'Logged in as %s' % session['username']
    return 'You are not logged in'


def check_credentials(username, password):
    db = get_db()
    cur = db.execute('select 1 from user where user_name = ? and user_password = ?', [username, password])

    if cur.fetchone():
        return True
    return False


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

@app.route('/chat/<int:task_id>')
def chat(task_id):
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

@app.route('/chat/save_chat', methods = ['POST'])
def save_chat():
    task_id = request.json['task_id']
    message_text = request.json['message_text']
    sender_id = get_user_id(session['username'])
    db = get_db()
    db.execute('insert into message values (NULL, ?, ?, ?)', [task_id, message_text, sender_id])
    db.commit()
    return Response("Saved")
