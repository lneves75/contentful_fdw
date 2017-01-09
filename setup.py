## This is a very simple setup for the module that allows us to create a foreign data wrapper in PostgreSQL to RethinkDB.
## It is based on the Multicorn README and the Hive FDW example.
##
from distutils.core import setup

setup(
  name='contentful_fdw',
  version='0.1',
  author='Rick Otten',
  author_email='rotten@windfish.net',
  license='Postgresql',
  packages=['contentful_fdw'],
  url='https://github.com/johanneswuerbach/contentful_fdw'
)
