Archer
======

Archer is a wiki, backed by SQLite and Mercurial.

Mercurial is used for version control, while SQLite is used for
reading unmodified pages and full-text search.


Getting Started
---------------

The short version:

    $ virtualenv ~/.virtualenvs/archer_env

    $ cd /path/to/archer && . ./.virtualenv

    $ pip install markdown flask html2text hglib
