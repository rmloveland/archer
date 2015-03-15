create table entries (
  id integer primary key autoincrement,
  uid  uuid text not null,
  title text not null,
  pretty_title text not null,
  text text not null,
  allowed_user_groups text
);

create table archived_entries (
  id integer primary key autoincrement,
  uid text not null,
  title text not null,
  pretty_title text not null,
  text text not null,
  allowed_user_groups text
);

create table users (
  id integer primary key autoincrement,
  uid text not null,
  username text not null,
  hashed_password text not null,
  recovery_email text not null,
  user_active_p integer default 0,
  user_group_id integer,
  foreign key(user_group_id) references user_groups(id)
);

create table user_groups (
  id integer primary key autoincrement,
  uid text not null,
  groupname text not null,
  user_group_active_p integer default 0
);
