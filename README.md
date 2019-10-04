# Archer

Archer is a Flask-based wiki, backed by SQLite and Git.

**This is a personal prototype that's not ready for other people to
use and you can safely ignore it.**

Python's programmatic Git interface is used for saving page edits into
version control, while SQLite is used for serving the pages up inside
the app, and full-text search.

License is [MIT](https://opensource.org/licenses/MIT).

## Overview

This is a prototype that grew out of me playing with the [Flask
Tutorial](http://flask.pocoo.org/docs/0.11/tutorial/).  I'm using it
to explore how to implement some ideas that are important in
multi-user documentation environments that might be important in a
professional setting.  Right now that includes:

+ user groups
+ access control to certain pages based on user group

In the future I'd like to work on features that would let me use it as
an "everything bucket" of sorts that I can run on DO or some other
service and access from anywhere.  Some features that would be cool to
have include:

+ tagging pages and adding different "views", such as "wiki
  view" or "issue tracker view"
+ See the file `DESIGN` in this directory for some random notes and
  ideas about where to go
+ REST API
+ web-facing query language similar to
  [JQL](http://blogs.atlassian.com/2013/01/jql-the-most-flexible-way-to-search-jira-14/?_ga=1.236371010.257445571.1472316705)
+ search
+ page history view
+ DB abstraction to move off of SQLite
+ oh yeah, tests

## Getting Started

Set the `ARCHER_DATA_DIR` env var to a Git repo where you want your
Markdown files to be stored.

    $ pip3 install markdown html2text flask gitpython
    $ export ARCHER_DATA_DIR=/Users/rloveland/Desktop/archer-files
    $ python3 archer.py

     * Serving Flask app "archer" (lazy loading)
     * Environment: production
    [31m   WARNING: This is a development server. Do not use it in a production deployment.[0m
    [2m   Use a production WSGI server instead.[0m
     * Debug mode: on
     * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
     * Restarting with stat
     * Debugger is active!
     * Debugger PIN: 12345
    127.0.0.1 - - [04/Oct/2019 16:32:20] "GET / HTTP/1.0" 200 -
    127.0.0.1 - - [04/Oct/2019 16:32:36] "GET /page/add HTTP/1.0" 200 -
    127.0.0.1 - - [04/Oct/2019 16:33:03] "POST /page/add HTTP/1.0" 302 -
    127.0.0.1 - - [04/Oct/2019 16:33:03] "GET /page/A-lightweight-query-language HTTP/1.0" 200 -
    127.0.0.1 - - [04/Oct/2019 16:33:23] "GET / HTTP/1.1" 200 -
    127.0.0.1 - - [04/Oct/2019 16:33:25] "GET /page/A-lightweight-query-language HTTP/1.1" 200 -
