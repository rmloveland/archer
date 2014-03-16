drop table if exists entries;

create table entries (
  id integer primary key autoincrement,
  title text not null,
  pretty_title text not null,
  text text not null
);

create table archived_entries (
  id integer primary key autoincrement,
  title text not null,
  pretty_title text not null,
  text text not null
);
