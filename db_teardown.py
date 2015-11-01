#!/usr/bin/env python

DB_FILES = {
    'DBFILE': 'flaskr.db',
    'SCHEMA': 'schema.sql'
}

stmt = '''
insert into users (
  uid,
  username,
  hashed_password,
  recovery_email,
  user_groups,
  user_active_p
)
values (
  "0001",
  "admin",
  "$pbkdf2-sha256$2000$FqL0HqP0PocQwvgfQwhhLA$vA.Whs0Z8SrFJVOPUxOGMNsyBiQcaM79cIC.k3/9vv4",
  "r@rmloveland.com",
  "admin_users",
  1
);
'''
