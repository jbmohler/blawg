create table gh_settings (
	-- singleton table enforced by primary key
	id integer primary key check (id=1),
	latest_sha text
);

insert into gh_settings (id)
values (1);

create table posts (
	id serial,
	gh_path text,
	post_title text,
	post_author text,
	post_date timestamptz
);

-- Consider making a non-admin PG role - e.g. blawguser
grant usage on schema public to blawguser;
grant select,insert,update,delete on all tables in schema public to blawguser;
grant usage,select,update on all sequences in schema public to blawguser;
