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

        if options.has_key('space'):
            self.space = options['space']
        else:
            log_to_postgres('space parameter is required.', ERROR)

        if options.has_key('api_key'):
            self.api_key = options['api_key']
        else:
            log_to_postgres('api_key parameter is required.', ERROR)

        if options.has_key('type'):
            self.type = options['type']
        else:
            log_to_postgres('type parameter is required.', ERROR)

        if options.has_key('content_type'):
            self.content_type = options['content_type']
        elif self.type == 'Entry':
            log_to_postgres('content_type parameter is required when using entries.', ERROR)

        self.columns = columns


    # SQL SELECT:
    def execute(self, quals, columns):

        log_to_postgres('Query Columns:  %s' % columns, DEBUG)
        log_to_postgres('Query Filters:  %s' % quals, DEBUG)

        client = contentful.Client(self.space, self.api_key)

        # By default, Multicorn seralizes dictionary types into something for hstore column types.
        # That looks something like this:   "key => value"
        # What we really want is this:  "{key:value}"
        # so we serialize it here.  (This is git issue #1 for this repo, and issue #86 in the Multicorn repo.)

        if self.type == 'ContentType':
            query = client.content_types()
            for result in query:
                row = OrderedDict()

                parseSys(row, result)

                row['name'] = result.name
                row['description'] = result.description
                row['display_field'] = result.display_field
                row['fields'] = json.dumps(list(map(lambda x: x.raw, result.fields))) # TODO: Can we do better?

                yield row
        elif self.type == 'Entry':
            query = client.entries({'content_type': self.content_type})

            for result in query:
                row = OrderedDict()

                parseSys(row, result)

                row['content_type'] = result.sys['content_type'].id

                for columnName in result.fields().keys():
                    row[columnName] = result.fields()[columnName]
    
                yield row
        elif self.type == 'Asset':
            query = client.assets()

            for result in query:
                row = OrderedDict()

                parseSys(row, result)

                fieldsMap = {
                    'title': 'title',
                    'description': 'description',
                    'file_name': 'file.fileName',
                    'file_content_type': 'file.contentType',
                    'file_url': 'file.url',
                    'file_size': 'file.details.size',
                }


                fields = result.fields()
                for key, value in fieldsMap.iteritems():
                    log_to_postgres('Getting fields %s => %s.' % (key, value), DEBUG)
                    row[key] = deepgetitem(fields, value)

                yield row
        else:
            log_to_postgres('Querying %s is not supported yet.' % self.type, ERROR)


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

def deepgetitem(obj, item, fallback=None):
    """Steps through an item chain to get the ultimate value.

    If ultimate value or path to value does not exist, does not raise
    an exception and instead returns `fallback`.

    >>> d = {'snl_final': {'about': {'_icsd': {'icsd_id': 1}}}}
    >>> deepgetitem(d, 'snl_final.about._icsd.icsd_id')
    1
    >>> deepgetitem(d, 'snl_final.about._sandbox.sbx_id')
    >>>
    """
    def getitem(obj, name):
        try:
            return obj[name]
        except (KeyError, TypeError):
            return None
    return reduce(getitem, item.split('.'), obj)

def parseSys(row, result):
    sysMap = {
        'id': 'id',
        'type': 'type'
    }

    for key, value in sysMap.iteritems():
        log_to_postgres('Mapping `sys.%s` to `%s`' % (value, key), DEBUG)
        row[key] = deepgetitem(result.sys, value)
