import requests
import sys
from re import sub

class invalidContentfulResponse(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)

class CMAClient(object):

	def __init__(
			self,
			space_id,
			access_token,
			api_url='api.contentful.com',
			api_version=1):
		self.space_id = space_id
		self.access_token = access_token
		self.api_url = api_url
		self.api_version = api_version

	def get_content_types(self, query=None):
		return self._request('get', '/content_types', query)

	def get_entries(self, query=None):
		return self._request('get', '/entries', query)

	def get_assets(self, query=None):
		return self._request('get', '/assets', query)

	def set_content_type(self, data, content_type_id=None, content_type_version=None):
		headers = {}
		if content_type_version:
			headers['X-Contentful-Version'] = str(content_type_version)

		if content_type_id:
			return self._request('put', '/content_types/%s' % content_type_id, data, headers)

		return self._request('post', '/content_types', data)

	def publish_content_type(self, content_type_id, content_type_version):
		headers = {}
		if content_type_version:
			headers['X-Contentful-Version'] = str(content_type_version)

		return self._request('put', '/content_types/%s/published' % content_type_id, {}, headers)

	def set_entry(self, content_type_id, data, entry_id=None, entry_version=None):
		headers = {
			'X-Contentful-Content-Type': content_type_id
		}
		if entry_version:
			headers['X-Contentful-Version'] = str(entry_version)

		if entry_id:
			return self._request('put', '/entries/%s' % entry_id, data, headers)

		return self._request('post', '/entries', data, headers)

	def set_asset(self, data, asset_id=None, asset_version=None):
		headers = {}
		if asset_version:
			headers['X-Contentful-Version'] = str(asset_version)

		if asset_id:
			return self._request('put', '/assets/%s' % asset_id, data, headers)

		return self._request('post', '/assets', data)

	def delete_content_type(self, id):
		return self._request('delete', '/content_types/%s' % content_type_id, data)

	def delete_entry(self, id):
		return self._request('delete', '/entries/%s' % content_type_id, data)

	def delete_asset(self, id):
		return self._request('delete', '/assets/%s' % content_type_id, data)

	def _request(self, method, url, data, additional_headers={}):
		headers = {**self._request_headers(), **additional_headers}

		url = self._url(url)

		if method == 'get':
			resp = requests.get(url, params=data, headers=headers)
		else:
		 	resp = getattr(requests, method)(url, json=data, headers=headers)

		if resp.status_code != 200 and resp.status_code != 201 and resp.status_code != 204:
			raise invalidContentfulResponse('%s failed (%s) \n%s.' % (method, resp.status_code, resp.text))

		return resp.json()

	def _request_headers(self):
		headers = {
			'Content-Type': 'application/vnd.contentful.delivery.v{0}+json'.format(  # noqa: E501
				self.api_version
			),
			'Authorization': 'Bearer {0}'.format(self.access_token),
			'Accept-Encoding': 'gzip'
		}

		return headers

	def _url(self, url):
		return 'https://{0}/spaces/{1}{2}'.format(
			self.api_url,
			self.space_id,
			url
		)
