drop table if exists entries;
create table entries (
  id text primary key,
  date_time text not null,
  'tweet' text not null
);
