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
create foreign table mytable (
    id varchar,
    type varchar,
    name varchar
 ) server mycontentfulspace options (table_name 'ignore');
SELECT * FROM mytable;
```
