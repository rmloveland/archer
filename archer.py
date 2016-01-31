#!/usr/bin/env python

import codecs
import hglib
import markdown
import markdown.extensions.attr_list
import markdown.extensions.tables
import markdown.extensions.toc
import os
import re
import sqlite3
import urllib
import uuid
from collections import namedtuple
from passlib.hash import pbkdf2_sha256
from flask import Flask, request, session, g
from flask import redirect, url_for, abort, render_template, flash

# Flask configuration stuff.

# Create our little application. :-)

app = Flask(__name__)
app.config.from_object(__name__)

# Load the default config and override it from an environment
# variable.

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'archer.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='admin',
    HGREPO=os.path.join(app.root_path, 'static/files/')
))

app.config.from_envvar('ARCHER_SETTINGS', silent=True)

# Database interactions.


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

    Note that 'g' represents the current application context in
    Flask.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """
    Closes the database again at the end of the request.

    Functions marked with the 'teardown_appcontext()' decorator are
    called every time the app context tears down.  The app context
    is created before the request comes in and is destroyed (torn down)
    whenever the request finishes.

    A teardown can happen for two reasons: (1) Everything went well, in
    which case the error parameter will be 'None'; (2) An exception
    occurred, in which case the error is passed to the teardown function.
    """
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

# Views.

# Showing all the entries.


@app.route('/')
def show_entries():
    """
    This view shows all the entries in the DB.  It listens on the root
    of the application and will select title and text from the DB.
    The newest entry (the highest ID) will be on top.  It will pass
    entries as dicts to the 'show_entries.html' template and return
    the rendered template.
    """
    if 'user_group_name' in session:
        user_group_name = session['user_group_name']
    else:
        user_group_name = ''
    entries = get_entries(user_group_name)
    return render_template('show_entries.html', entries=entries)

# Viewing entries.


@app.route('/page/<title>', methods=['GET'])
def view_entry(title):
    """
    View a single entry by itself, on its own page.
    """
    if session:
        user_group_name = session['user_group_name']
        user_group_list = user_group_name.split(',')
    else:
        user_group_name = ''
        user_group_list = []

    user_group_list.sort()
    user_group = user_group_list[0]
    db = get_db()
    if 'admin_users' in user_group_list:
        stmt = '''
        select title, pretty_title, text, allowed_user_groups
        from entries where pretty_title like ?
        '''
        cur = db.execute(stmt, ['%' + title + '%'])
    else:
        stmt = '''
        select title, pretty_title, text, allowed_user_groups
        from entries where
        pretty_title like ? and allowed_user_groups like ?
        '''
        cur = db.execute(stmt, ('%' + title + '%', '%' + user_group + '%'))
    the_entries = cur.fetchall()

    # FIXME: This is the bug that keeps admin users from seeing everything
    entry = the_entries[0]
    entry_text = entry['text']
    entry_html = markdown.markdown(
        entry_text,
        extensions=[
            'markdown.extensions.attr_list',
            'markdown.extensions.tables',
            'markdown.extensions.toc'
            ]
        )
    entries = get_entries(user_group_name)
    return render_template(
        'view_entry.html',
        entry=entry,
        entries=entries,
        entry_html=entry_html
    )

# Adding entries.


@app.route('/page/add', methods=['GET'])
def show_add_entry():
    """
    This view just renders the 'add an entry' page.
    """
    user_group_name = session['user_group_name']
    entries = get_entries(user_group_name)
    return render_template('add_entry.html', entries=entries)


@app.route('/page/add', methods=['POST'])
def add_entry():
    """
    This view lets the user add new entries if they are logged
    in.  This only responds to POSTs.  If everything worked, we
    will FLASH() an informational message to the next request
    and redirect to the SHOW_ENTRIES page.
    """
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    text = request.form['text']
    text.encode('utf-8').strip()
    raw_title = request.form['title']
    prettified_title = prettify(raw_title)
    uid = uuid.uuid4()
    already_allowed = 'admin_users'
    allowed_by_page = request.form['allowed_user_groups']
    allowed_by_page = re.sub(' ', '', allowed_by_page)
    tmp1 = already_allowed + ',' + allowed_by_page
    tmp2 = tmp1.split(',')
    allowed_list = uniquify(tmp2)
    allowed_string = ','.join(allowed_list)
    stmt = '''
    insert into entries
    (title, pretty_title, text, uid, allowed_user_groups)
    values (?, ?, ?, ?, ?)
    '''
    db.execute(stmt,
               [raw_title, prettified_title, text, uid.hex, allowed_string])
    db.commit()
    store(prettified_title, text, addFile=True)
    flash('A new entry was successfully posted!')
    return redirect(url_for('view_entry', title=prettified_title))


def touch_file(filepath):
    fname = filepath
    with codecs.open(fname, 'w', 'utf-8') as f:
        f.write('')


def store(title, text, addFile=False):
    # TODO: now that we can have pages with the same titles, we should store
    # the pages as a combination of path and UID (or something).
    repo_path = os.path.abspath(app.config['HGREPO'])
    pretty_title = prettify(title)
    user = app.config['USERNAME']
    file_path = os.path.join(repo_path, pretty_title)
    text.encode('utf-8')
    client = hglib.open(repo_path)
    if not os.path.exists(file_path):
        touch_file(file_path)
    with codecs.open(file_path, 'w', 'utf-8') as fout:
        fout.write(text)
    if addFile:
        client.add(file_path)
    if client.diff():
        client.commit(
            'Change to "{}".'.format(pretty_title),
            addremove=True,
            user=user
        )
    client.close()

# Archiving entries.


@app.route('/archive/<title>', methods=['GET'])
def archive_entry(title):
    """
    """
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    # Archive it
    stmt = '''
    insert into archived_entries select * from entries
    where pretty_title like ?
    '''
    db.execute(stmt,
               ('%' + title + '%',))
    db.execute('delete from entries where pretty_title like ?',
               ('%' + title + '%',))
    db.commit()
    flash('Archived page: ' + title)
    return redirect(url_for('show_entries'))

# Editing entries.


@app.route('/edit/<title>', methods=['GET'])
def show_edit_entry(title):
    """
    This view just renders the 'edit an entry' page.
    """
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    stmt = '''
    select title, pretty_title, text, allowed_user_groups
    from entries where pretty_title like ?
    '''
    cur = db.execute(stmt,
                     ('%' + title + '%',))
    entries = cur.fetchall()
    entry = entries[0]
    markdown_text = entry[2]
    # allowed_user_groups = entry[3]
    user_group_name = session['user_group_name']
    entries = get_entries(user_group_name)
    return render_template(
        'edit_entry.html',
        entry=entry,
        markdown_text=markdown_text,
        entries=entries

    )


@app.route('/edit/<title>', methods=['POST'])
def edit_entry(title):
    """
    This view lets the user actually save their edits to an entry.
    """
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    text = request.form['text']
    allowed_user_groups = request.form['allowed_user_groups']
    text.encode('utf-8').strip()
    stmt = '''
    update entries set text=?, allowed_user_groups=? where pretty_title like ?
    '''
    db.execute(
        stmt,
        (text, allowed_user_groups, '%' + title + '%')
    )
    db.commit()
    store(title, text)
    flash('Saved your edits')
    return redirect(url_for('view_entry', title=title))

# Authentication.  Logging in and out.


@app.route('/users/login', methods=['GET', 'POST'])
def login():
    """
    Checks the user's credentials against those from the
    configuration and sets the 'logged_in' key in the
    session.
    """
    error = None
    if request.method == 'POST':
        raw_username = request.form['username']
        raw_password = request.form['password']
        user_group_name = ''  # FIXME ?
        if raw_username is 'admin' and raw_password is 'admin':
            session['logged_in'] = True
            session['username'] = raw_username
            session['user_group_name'] = user_group_name
            flash('You were logged in')
            return redirect(url_for('show_entries'))
        hashed_password = get_hashed_password(raw_username)
        if hashed_password:
            user_group_name = get_user_group_name(raw_username)
            if not pbkdf2_sha256.verify(raw_password, hashed_password):
                error = 'invalid username or password'
            else:
                session['logged_in'] = True
                session['username'] = raw_username
                session['user_group_name'] = user_group_name
                flash('You were logged in')
                return redirect(url_for('show_entries'))
        else:
            flash('incorrect username or password')
    if 'user_group_name' in session:
        user_group_name = session['user_group_name']
    else:
        user_group_name = ''
    entries = get_entries(user_group_name)
    return render_template('login.html', error=error, entries=entries)


def get_user_group_name(username):
    db = get_db()
    cur = db.execute(
        'select user_groups from users where username == ?',
        [username]
    )
    entries = cur.fetchall()
    entry = entries[0]
    user_group_name = entry['user_groups']
    return user_group_name


def get_hashed_password(username):
    db = get_db()
    cur = db.execute(
        'select hashed_password from users where username like (?)',
        [username]
    )
    entries = cur.fetchall()
    if entries:
        entry = entries[0]
        hashed_password = entry['hashed_password']
    else:
        hashed_password = False

    return hashed_password

# Creating users.


@app.route('/users/add', methods=['GET'])
def show_add_user():
    '''
    This view just renders the 'add a user' page.
    '''
    user_group_name = session['user_group_name']
    if not user_group_name == 'admin_users':
        abort(401)

    entries = get_entries(user_group_name)
    return render_template('add_user.html', entries=entries)


@app.route('/users/add', methods=['POST'])
def add_user():
    username = request.form['username']
    text_password = request.form['password']
    hashed_password = pbkdf2_sha256.encrypt(
        text_password,
        rounds=2000,
        salt_size=16
    )
    recovery_email = request.form['email']
    user_groups = request.form['user_groups']
    uid = uuid.uuid4()
    user_active_p = True
    db = get_db()
    stmt = '''
    insert into users (
    uid, username, hashed_password, recovery_email, user_groups, user_active_p
    ) values (?, ?, ?, ?, ?, ?)
    '''
    db.execute(stmt, [
        uid.hex,
        username,
        hashed_password,
        recovery_email,
        user_groups,
        user_active_p
        ])
    db.commit()
    flash('A new user was successfully posted!')
    return redirect(url_for('show_entries'))


def make_user(username, password, email, groups, user_active_p=True):
    # -> User
    User = namedtuple(
        'User',
        [
            'username',
            'text_password',
            'hashed_password',
            'recovery_email',
            'user_groups',
            'uid',
            'user_active_p'
        ]
    )
    the_user = User(
        username,
        password,
        pbkdf2_sha256.encrypt(
            password,
            rounds=2000,
            salt_size=16
        ),
        email,
        groups,
        uuid.uuid4(),
        user_active_p
    )
    return the_user

# (R)eading users.


@app.route('/users', methods=['GET'])
def show_users():
    '''Show a list of all users.'''
    user_group_name = session['user_group_name']
    if not user_group_name == 'admin_users':
        abort(401)
    entries = get_entries(user_group_name)
    users = get_users()
    return render_template('show_users.html', entries=entries, users=users)


@app.route('/users/logout')
def logout():
    """
    Uses one neat trick to log the user out. If we use the POP method of
    the dict and pass a second parameter, the method will delete the
    key if present, or do nothing if the key is not there.  This means
    we don't have to explicitly check if the user is logged in.
    """
    session.clear()
    session['user_group_name'] = ''
    flash('You were logged out')
    return redirect(url_for('show_entries'))

# Utilities.


def uniquify_sqlite_row_objects(xs):
    results = []
    seen = {}
    for x in xs:
        title = x['pretty_title']
        if title not in seen:
            results.append(x)
        seen[title] = 1
    return results


def uniquify(xs):
    uniq = []
    for x in set(xs):
        uniq.append(x)
    return uniq


def prettify(encoded_title):
    first = re.sub('[ ,\'\?!]', '-', urllib.unquote(encoded_title))
    second = re.sub('--', '-', urllib.unquote(first))
    return re.sub('-$', '', urllib.unquote(second))


def get_entries(user_group_name):
    db = get_db()
    if user_group_name == '':
        return []

    user_groups = user_group_name.split(',')
    total_entries = []

    # TODO: This "fixes" things for non-admin users (by removing redundant
    # titles), but breaks things for admin users, since as an admin user I
    # should be able to see all of the entries with the same name.

    for group in user_groups:
        if 'admin_users' in user_groups:
            cur = db.execute("select title, pretty_title, text from entries")
        else:
            stmt = '''
            select title, pretty_title, text
            from entries where allowed_user_groups like ?
            '''
            cur = db.execute(stmt, ['%' + group + '%'])
        entries = cur.fetchall()
        for entry in entries:
            total_entries.append(entry)

    unique_entries = uniquify_sqlite_row_objects(total_entries)

    if 'admin_users' in user_groups:
        return total_entries
    else:
        return unique_entries


def get_users():
    db = get_db()
    stmt = '''
    select id, uid, user_groups, username from users order by id asc
    '''
    cur = db.execute(stmt)
    users = cur.fetchall()
    return users

# Run the program.

if __name__ == '__main__':
    app.run()
