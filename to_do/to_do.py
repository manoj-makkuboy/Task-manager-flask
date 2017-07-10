import os
import sqlite3
from flask import Flask, request,  g, redirect, url_for,   flash, Response
from flask import current_app
import json

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
    cur = db.execute('select task_id,item_content, is_done from entries order by task_id asc')
    entries = cur.fetchall()
    json_array = []
    for entry in entries:
        json_array.append([x for x in entry])
    return Response(json.dumps(json_array), mimetype='json/application')


@app.route('/add', methods=['POST'])
def add_entry():
    recievedJSON = request.json
    db = get_db()
    db.execute('insert into entries (item_content, is_done) values (?, ?)', [recievedJSON[0], recievedJSON[1]])
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

    db.execute('update entries set is_done = ? where task_id=?', [is_done, task_id])

    db.commit()
    flash('update successful')
    return show_entries()   # sends Response() the entire JSON from serverside


@app.route('/delete', methods = ['POST'])
def delete_task():
    task_id = request.json
    db = get_db()
    db.execute('delete from entries where task_id = ?', [task_id])
    db.commit()
    return show_entries()


@app.route('/assign', methods=['POST'])
def assign_task():
    task_id = request.json[0]
    assignee = request.json[1]
    assignee_id = 0
    db = get_db()
    cur = db.execute('select user_id from user where user_name = ?', [assignee])
    entries = cur.fetchall()
    for entry in entries:
        for data in entry:
            assignee_id = data
    db.execute('insert into assignment values (NULL, ?, ?, ?)', [task_id, 1, assignee_id])
    db.commit()
    return show_entries()


@app.route('/')
def to_do():
    return current_app.send_static_file('using_js.html')
