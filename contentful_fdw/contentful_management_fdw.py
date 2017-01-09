## This is the implementation of the Multicorn ForeignDataWrapper class
## Adapted from https://github.com/rotten/rethinkdb-multicorn-postgresql-fdw

from collections import OrderedDict
import json
import functools

from multicorn import ForeignDataWrapper
from multicorn.utils import log_to_postgres, ERROR, WARNING, DEBUG

from .operator_map import unknownOperatorException, getOperatorFunction
from .cma_client import invalidContentfulResponse, CMAClient


## The Foreign Data Wrapper Class:
class ContentfulManagementFDW(ForeignDataWrapper):

	"""
	Contentful Management FDW for PostgreSQL
	"""

	def __init__(self, options, columns):

		super(ContentfulManagementFDW, self).__init__(options, columns)

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

		self.client = CMAClient(self.space, self.api_key)

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
			results = self.client.get_content_types(query)

			for result in results['items']:
				row = parseContentType(result)

				yield row
		elif self.type == 'Entry':
			query['content_type'] = self.content_type

			results = self.client.get_entries(query)

			for result in results['items']:
				row = parseEntry(result)

				yield row
		elif self.type == 'Asset':
			results = self.client.get_assets(query)

			for result in results['items']:
				row = parseAsset(result)

				yield row
		else:
			log_to_postgres('Querying %s is not supported yet.' % self.type, ERROR)


	# SQL INSERT:
	def insert(self, values):
		log_to_postgres('Insert Request - new values:  %s' % values, DEBUG)

		if 'id' in values:
			entity_id = values['id']
			del values['id']

		try:
			if self.type == 'ContentType':
				log_to_postgres('Insert payload (%s).' % (json.dumps(values)), DEBUG)

				resp = self.client.set_content_type(stringifyContentType(values), entity_id)

				return parseContentType(resp)
			elif self.type == 'Entry':
				r = stringifyEntry(values)
				log_to_postgres('E:  %s' % json.dumps(r), DEBUG)
				resp = self.client.set_entry(self.content_type, stringifyEntry(values), entity_id)

				return parseEntry(resp)
			elif self.type == 'Asset':
				resp = self.client.set_asset(stringifyAsset(values), entity_id)

				return parseAsset(resp)
			else:
				log_to_postgres('Inserting entities of type %s is not supported yet.' % self.type, ERROR)
		except invalidContentfulResponse as e:
			log_to_postgres(e, ERROR)

	# SQL UPDATE:
	def update(self, rowid, new_values):
		log_to_postgres('Update Request - new values:  %s' % new_values, DEBUG)

		if not rowid:
			 log_to_postgres('Update request requires rowid (PK).', ERROR)

		if 'version' in new_values:
			entity_version = new_values['version']
			del new_values['version']

		if 'published' in new_values:
			published = new_values['published']
			del new_values['published']

		try:
			if self.type == 'ContentType':
				resp = self.client.set_content_type(stringifyContentType(new_values), rowid, entity_version)

				if published == 't':
					log_to_postgres('Publishing content type %s.' % rowid, DEBUG)
					self.client.publish_content_type(rowid, entity_version+1)

				return parseContentType(resp)
			elif self.type == 'Entry':
				resp = self.client.set_entry(stringifyEntry(new_values), rowid, entity_version)

				return parseEntry(resp)
			elif self.type == 'Asset':
				resp = self.client.set_asset(stringifyAsset(new_values), rowid, entity_version)

				return parseAsset(resp)
			else:
				log_to_postgres('Updating entities of type %s is not supported yet.' % self.type, ERROR)
		except invalidContentfulResponse as e:
			log_to_postgres(e, ERROR)

	# SQL DELETE
	def delete(self, rowid):
		log_to_postgres('Delete Request - rowid:  %s' % rowid, DEBUG)

		if not rowid:
			log_to_postgres('Update request requires rowid (PK).', ERROR)

		try:
			if self.type == 'ContentType':
				self.client.delete_content_type(rowid)
			elif self.type == 'Entry':
				self.client.delete_entry(rowid)
			elif self.type == 'Asset':
				self.client.delete_asset(rowid)
			else:
				log_to_postgres('Deleting entities of type %s is not supported yet.' % self.type, ERROR)
		except invalidContentfulResponse as e:
			log_to_postgres(e, ERROR)

		return {}

	@property
	def rowid_column(self):
		log_to_postgres('rowid requested', DEBUG)

		return 'id'

def deepgetitem(obj, item):
	"""Steps through an item chain to get the ultimate value.

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

def deepsetitem(obj, item, value):
	keys = item.split('.')
	last_key = keys.pop()

	def setitem(obj, name):
		if name not in obj:
			obj[name] = {}
		return obj[name]
	obj = functools.reduce(setitem, keys, obj)
	obj[last_key] = value

def parseSys(row, result):
	sysMap = {
		'id' : 'sys.id',
		'type': 'sys.type',
		'version': 'sys.version',
		'published_version': 'sys.publishedVersion'
	}

	for key, value in sysMap.items():
		row[key] = deepgetitem(result, value)

def parseAsset(result):
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

	for key, value in fieldsMap.items():
		row[key] = deepgetitem(result, value)

	return row

def parseContentType(result):
	row = OrderedDict()
	parseSys(row, result)

	fieldsMap = {
		'name': 'name',
		'description': 'description'
	}

	for key, value in fieldsMap.items():
		row[key] = deepgetitem(result, value)

	if 'fields' in result:
		row['fields'] = json.dumps(result['fields'])

	return row

def parseEntry(result):
	row = OrderedDict()
	parseSys(row, result)

	fieldsMap = {
		'content_type': 'sys.contentType.sys.id'
	}

	for key, value in fieldsMap.items():
		row[key] = deepgetitem(result, value)

	fields = result['fields']
	for columnName in fields.keys():
		row[columnName] = fields[columnName]['en-US']

	return row

def stringifyAsset(row):
	result = OrderedDict()

	fieldsMap = {
		'title': 'fields.title',
		'description': 'fields.description',
		'file_name': 'fields.file.fileName',
		'file_content_type': 'fields.file.contentType',
		'file_url': 'fields.file.url',
		'file_size': 'fields.file.details.size',
	}

	for key, value in fieldsMap.items():
		if key not in row:
			continue
		deepsetitem(result, value, row[key])

	return result

def stringifyContentType(row):
	result = OrderedDict()

	fieldsMap = {
		'name': 'name',
		'description': 'description'
	}

	for key, value in fieldsMap.items():
		if key not in row:
			continue
		deepsetitem(result, value, row[key])

	if 'fields' in row:
		result['fields'] = json.loads(row['fields'])

	return result

def stringifyEntry(row):
	result = OrderedDict()

	for key, value in row.items():
		if key in ['id', 'version', 'type', 'content_type']:
			continue
		deepsetitem(result, 'fields.%s.en-US' % key, row[key])

	return result

def translateQueryField(field):
	sysFields = {
		'id' : 'sys.id',
		'type': 'sys.type'
	}

	if field in sysFields:
		return sysFields[field]

	return 'fields.%s' % field
