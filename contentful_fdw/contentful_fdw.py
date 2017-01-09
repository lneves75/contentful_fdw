## This is the implementation of the Multicorn ForeignDataWrapper class
## Adapted from https://github.com/rotten/rethinkdb-multicorn-postgresql-fdw

from collections import OrderedDict
import json

from multicorn import ForeignDataWrapper
from multicorn.utils import log_to_postgres, ERROR, WARNING, DEBUG

import contentful


## The Foreign Data Wrapper Class:
class ContentfulFDW(ForeignDataWrapper):

    """
    Contentful FDW for PostgreSQL
    """

    def __init__(self, options, columns):

        super(ContentfulFDW, self).__init__(options, columns)

        log_to_postgres('options:  %s' % options, DEBUG)
        log_to_postgres('columns:  %s' % columns, DEBUG)

        # if options.has_key('host'):
        #     self.host = options['host']
        # else:
        #     self.host = 'localhost'
        #     log_to_postgres('Using Default host:  localhost.', WARNING)
        #
        # if options.has_key('port'):
        #     self.port = options['port']
        # else:
        #     self.port = '28015'
        #     log_to_postgres('Using Default port: 28015.', WARNING)
        #
        # if options.has_key('database'):
        #     self.database = options['database']
        # else:
        #     log_to_postgres('database parameter is required.', ERROR)
        #
        # if options.has_key('table_name'):
        #     self.table = options['table_name']
        # else:
        #     log_to_postgres('table_name parameter is required.', ERROR)

        # if options.has_key('auth_key'):
        #     self.auth_key = options['auth_key']
        # else:
        #     log_to_postgres('auth_key parameter is required.', ERROR)

        self.columns = columns


    # SQL SELECT:
    def execute(self, quals, columns):

        log_to_postgres('Query Columns:  %s' % columns, DEBUG)
        log_to_postgres('Query Filters:  %s' % quals, DEBUG)

        client = contentful.Client('cfexampleapi', 'b4c0n73n7fu1')

        # By default, Multicorn seralizes dictionary types into something for hstore column types.
        # That looks something like this:   "key => value"
        # What we really want is this:  "{key:value}"
        # so we serialize it here.  (This is git issue #1 for this repo, and issue #86 in the Multicorn repo.)

        for resultRow in client.content_types():

            # I don't think we can mutate the row in the rethinkResults cursor directly.
            # It needs to be copied out of the cursor to be reliably mutable.
            row = OrderedDict()

            row['id'] = resultRow.id
            row['name'] = resultRow.name
            row['type'] = resultRow.type

            yield row


    # # SQL INSERT:
    # def insert(self, new_values):
    #
    #     log_to_postgres('Insert Request - new values:  %s' % new_values, DEBUG)
    #
    #     return self._run_rethinkdb_action(action=r.table(self.table)\
    #                                               .insert(new_values))
    #
    # # SQL UPDATE:
    # def update(self, rowid, new_values):
    #
    #     log_to_postgres('Update Request - new values:  %s' % new_values, DEBUG)
    #
    #     if not rowid:
    #
    #          log_to_postgres('Update request requires rowid (PK).', ERROR)
    #
    #     return self._run_rethinkdb_action(action=r.table(self.table)\
    #                                               .get(rowid)\
    #                                               .update(new_values))
    #
    # # SQL DELETE
    # def delete(self, rowid):
    #
    #     log_to_postgres('Delete Request - rowid:  %s' % rowid, DEBUG)
    #
    #     if not rowid:
    #
    #         log_to_postgres('Update request requires rowid (PK).', ERROR)
    #
    #     return self._run_rethinkdb_action(action=r.table(self.table)\
    #                                               .get(rowid)\
    #                                               .delete())


    def rowid_column(self, rowid):

        log_to_postgres('rowid requested', DEBUG)

        return 'id'
