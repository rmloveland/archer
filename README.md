Archer
======

Archer is a Flask-based wiki, backed by SQLite and Mercurial.

Python's programmatic Mercurial interface is used for saving page
edits into version control, while SQLite is used for serving the pages
up inside the app, and full-text search.

Basically this is a personal prototype that's not ready for other
people to use; you can safely ignore it.

Overview
--------

This is a prototype that grew out of me playing with the
[Flask Tutorial](http://flask.pocoo.org/docs/0.11/tutorial/).  I'm
using it to explore how to implement some ideas that are important in
multi-user documentation environments that might be important in a
professional setting.  Right now that includes:

+ user groups
+ access control to certain pages based on user group

In the future I'd like to work on features that would let me use it as an "everything bucket" of sorts that I can run on DO or some other service and access from anywhere.  Some features that would be cool to have include:

+ tagging pages and adding different "views", such as "wiki
  view" or "issue tracker view"
+ See the file `DESIGN` in this directory for some random notes and
  ideas about where to go
+ REST API
+ web-facing query language similar to [JQL](http://blogs.atlassian.com/2013/01/jql-the-most-flexible-way-to-search-jira-14/?_ga=1.236371010.257445571.1472316705)
+ search
+ page history view
+ DB abstraction to move off of SQLite
+ oh yeah, tests

Getting Started
---------------

Right now it uses Python 2.7, I don't know if it works with Python 3.

The short version:

    $ virtualenv ~/.virtualenvs/archer_env

    $ cd /path/to/archer && . ./.virtualenv

    $ pip install markdown flask html2text hglib
