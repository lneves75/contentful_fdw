.PHONY: build

# Build postgres + contentfdw docker image
build:
	docker build -t contentful_fdw .

# Run postgres + contentfdw docker image
run:
	docker run --rm -p 5432:5432 -v $(PWD):/app --name contentful_fdw contentful_fdw

# TODO: Not working :-(
reload:
	docker exec contentful_fdw bash -c "python setup.py install"
	docker exec contentful_fdw bash -c "su-exec postgres pg_ctl reload"
