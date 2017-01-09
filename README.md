# contentful_fdw

Required: docker

```bash
make build run
```

## Delivery

```sql
drop extension if exists multicorn cascade;

create extension multicorn;

create server mycontentfulspace foreign data wrapper multicorn options (
	wrapper 'contentful_fdw.contentful_fdw.ContentfulFDW',
	space 'cfexampleapi',
	api_key 'b4c0n73n7fu1'
);

create foreign table content_types (
  id varchar,
  type varchar,
  name varchar,
  description varchar,
  display_field varchar,
  fields jsonb
) server mycontentfulspace options (type 'ContentType');

create foreign table cat_entries (
  id varchar,
  type varchar,
  content_type varchar,
  name varchar,
  color varchar,
  birthday date,
  lifes numeric,
  image varchar
) server mycontentfulspace options (type 'Entry', content_type 'cat');

create foreign table assets (
  id varchar,
  type varchar,
  title varchar,
  description varchar,
  file_name varchar,
  file_content_type varchar,
  file_url varchar,
  file_size numeric
) server mycontentfulspace options (type 'Asset');

SELECT * FROM content_types;

SELECT * FROM cat_entries WHERE id != 'nyancat';

SELECT cat_entries.id, cat_entries.name, assets.file_url FROM cat_entries, assets WHERE cat_entries.image = assets.id;
```

## Management

```sql
drop extension if exists multicorn cascade;

create extension multicorn;

create server mycontentfulspace foreign data wrapper multicorn options (
	wrapper 'contentful_fdw.contentful_management_fdw.ContentfulManagementFDW',
	space 'xxxx',
	api_key 'yyyy'
);

create foreign table content_types (
  id varchar,
  type varchar,
  name varchar,
  version integer,
  published_version integer,
  description varchar,
  display_field varchar,
  fields jsonb,
  published boolean
) server mycontentfulspace options (type 'ContentType');

insert into content_types (id, name, description, fields) VALUES ('post-ct', 'name', 'test', '[{"id":"title","name":"title","required":true,"localized":true,"type":"Text"},{"id":"body","name":"body","required":true,"localized":true,"type":"Text"}]');

select * from content_types where id = 'post-ct';

update content_types set name = 'changed name' where id = 'post-ct';

update content_types set published = true where id = 'post-ct';

create foreign table post_entries (
  id varchar,
  content_type varchar,
  title varchar,
  body varchar
) server mycontentfulspace options (type 'Entry', content_type 'post-ct');

select * from post_entries;

insert into post_entries (title, body) VALUES ('test', 'some long posting...');

select * from post_entries;
```
