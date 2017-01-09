## This is the implementation of the Multicorn ForeignDataWrapper class
## Adapted from https://github.com/rotten/rethinkdb-multicorn-postgresql-fdw

from collections import OrderedDict
import json
import functools

from multicorn import ForeignDataWrapper
from multicorn.utils import log_to_postgres, ERROR, WARNING, DEBUG

from .operator_map import unknownOperatorException, getOperatorFunction

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

		if 'space' in options:
			self.space = options['space']
		else:
			log_to_postgres('space parameter is required.', ERROR)

		if 'api_key' in options:
			self.api_key = options['api_key']
		else:
			log_to_postgres('api_key parameter is required.', ERROR)

		if 'type' in options:
			self.type = options['type']
		else:
			log_to_postgres('type parameter is required.', ERROR)

		if 'content_type' in options:
			self.content_type = options['content_type']
		elif self.type == 'Entry':
			log_to_postgres('content_type parameter is required when using entries.', ERROR)

		self.client = contentful.Client(self.space, self.api_key)

		self.columns = columns

	# SQL SELECT:
	def execute(self, quals, columns):
		log_to_postgres('Query Columns:  %s' % columns, DEBUG)
		log_to_postgres('Query Filters:  %s' % quals, DEBUG)

		# Translate query
		query = {}

		for qual in quals:
			try:
				operator = getOperatorFunction(qual.operator)
			except unknownOperatorException as e:
				log_to_postgres(e, ERROR)

			query[translateQueryField(qual.field_name) + operator] = qual.value

		log_to_postgres('Translated query: %s' % (json.dumps(query)), DEBUG)

		if self.type == 'ContentType':
			results = self.client.content_types(query)
			for result in results:
				row = OrderedDict()

				parseSys(row, result)

				row['name'] = result.name
				row['description'] = result.description
				row['display_field'] = result.display_field
				row['fields'] = json.dumps(list(map(lambda x: x.raw, result.fields))) # TODO: Can we do better?

				yield row
		elif self.type == 'Entry':
			query['content_type'] = self.content_type
			results = self.client.entries(query)

			for result in results:
				row = OrderedDict()

				parseSys(row, result)

				row['content_type'] = result.sys['content_type'].id

				fields = result.fields()
				for columnName in fields.keys():
					if type(fields[columnName]) is contentful.Asset:
						row[columnName] = fields[columnName].id
					elif type(fields[columnName]) is contentful.Entry:
						row[columnName] = fields[columnName].id
					else:
						row[columnName] = fields[columnName]

				yield row
		elif self.type == 'Asset':
			results = self.client.assets(query)

			for result in results:
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
				for key, value in fieldsMap.items():
					log_to_postgres('Getting fields %s => %s.' % (key, value), DEBUG)
					row[key] = deepgetitem(fields, value)

				yield row
		else:
			log_to_postgres('Querying %s is not supported yet.' % self.type, ERROR)

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
	return functools.reduce(getitem, item.split('.'), obj)

def parseSys(row, result):
	sysMap = {
		'id': 'id',
		'type': 'type'
	}

	for key, value in sysMap.items():
		log_to_postgres('Mapping `sys.%s` to `%s`' % (value, key), DEBUG)
		row[key] = deepgetitem(result.sys, value)

def translateQueryField(field):
	sysFields = {
		'id' : 'sys.id',
		'type': 'sys.type'
	}

	if field in sysFields:
		return sysFields[field]

	return 'fields.%s' % field
