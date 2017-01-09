.PHONY: build

# Build postgres + contentfdw docker image
build:
	docker build -t contentful_fdw .

# Run postgres + contentfdw docker image
run:
	docker run --rm -p 5432:5432 -v $(PWD):/app --name contentful_fdw contentful_fdw

# Rebuild extension and terminate all connections to force reload
reload:
	docker exec contentful_fdw bash -c "python setup.py install"
	docker exec contentful_fdw bash -c "su-exec postgres pg_ctl reload"
	docker exec contentful_fdw bash -c "psql -U postgres -c 'SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid();'"
