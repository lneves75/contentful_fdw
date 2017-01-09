# contentful_fdw

Required: docker

```bash
make build run
```

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
