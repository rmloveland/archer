#!/usr/bin/env python

import os, sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

# Create our little application. :-)
app = Flask(__name__)
app.config.from_object(__name__)

# Load the default configuration and override it from an environment
# variable.
app.config.update(dict(
    DATABASE = os.path.join(app.root_path, 'flaskr.db'),
    DEBUG = True,
    SECRET_KEY = 'development key',
    USERNAME = 'admin',
    PASSWORD = 'default'
))

app.config.from_envvar('FLASKR_SETTINGS', silent=True)

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def init_db():
    """
    Initialize the database from our schema file.

    In this case we don't have an application context yet, since
    no request has come in.  Therefore we need to create the
    context by hand.
    """
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    """
    Opens a new database connection if there isn't one yet available
    for the current application context.

    Note that `g' represents the current application context in
    Flask.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """
    Closes the database again at the end of the request.

    Functions marked with the `teardown_appcontext()' decorator are
    called every time the app context tears down.  The app context
    is created before the request comes in and is destroyed (torn down)
    whenever the request finishes.

    A teardown can happen for two reasons: (1) Everything went well, in
    which case the error parameter will be `None'; (2) An exception
    occurred, in which case the error is passed to the teardown function.
    """
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


### The 4 views of the application.

## View 1. Show all entries.

@app.route('/')
def show_entries():
    """
    This view shows all the entries in the DB.  It listens on the root
    of the application and will select title and text from the DB.
    The newest entry (the highest ID) will be on top.  It will pass
    entries as dicts to the `show_entries.html' template and return
    the rendered template.
    """
    db = get_db()
    cur = db.execute('select title, text from entries order by id desc')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)

## View 2. Add a new entry.

@app.route('/add', methods=['POST'])
def add_entry():
    """
    This view lets the user add new entries if they are logged
    in.  This only responds to POSTs.  If everything worked, we
    will `flash()' an informational message to the next request
    and redirect to the `show_entries' page.
    """
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into entries (title, text) values (?, ?)',
               [request.form['title'], request.form['text']])
    db.commit()
    flash('A new entry was successfully posted!')
    return redirect(url_for('show_entries'))

## Views 3 and 4. Log in and out.

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Checks the user's credentials against those from the
    configuration and sets the `logged_in' key in the
    session.
    """
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    """
    Uses one neat trick to log the user out. If we use the POP method of
    the dict and pass a second parameter, the method will delete the
    key if present, or do nothing if the key is not there.  This means
    we don't have to explicitly check if the user is logged in.
    """
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

if __name__ == '__main__':
    app.run()
