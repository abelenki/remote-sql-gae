# -*- encoding: utf-8 -*-

# Copyright 2012 Artyom Maslovsky

#  This file is part of RemoteSQL-GAE.
#
#  RemoteSQL-GAE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  RemoteSQL-GAE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with RemoteSQL-GAE.  If not, see <http://www.gnu.org/licenses/>.

import webapp2
import json
import cgi

import models

def auth(method):
	AUTH_TOKEN = 'caf0ab246d8649580665683653f6825a'

	def wrapper(self, *pargs, **kwargs):
		if 'auth' in self.request.cookies:
			if self.request.cookies['auth'] == AUTH_TOKEN:
				return method(self, *pargs, **kwargs)
			else:
				self.error(401)
		else:
			self.error(401)

	return wrapper



class Error400: pass

def catch_errors(method):

	def wrapper(self, *pargs, **kwargs):
		try:
			return method(self, *pargs, **kwargs)
		except:
			self.error(400)

	return wrapper

def common_headers(method):

	def wrapper(self, *pargs, **kwargs):
		self.response.headers['Connection'] = 'close'
		self.response.headers['Content-Type'] = 'application/json'

		return method(self, *pargs, **kwargs)

	return wrapper


class RemoteSQLServer(webapp2.RequestHandler):

	@auth
	@catch_errors
	@common_headers
	def get(self):
		"""
		SELECT ... FROM ...
		"""

		objects = self.get_filtered_objects()

		result = []
		for obj in objects.fetch(objects.count()):
			obj_dir = {}
			for key in obj._fields:
				if not key.startswith('_'):
					obj_dir[key] = obj.__getattribute__(key)
			result.append(obj_dir)

		self.response.out.write(json.dumps(result))

	@auth
	@catch_errors
	@common_headers
	def post(self):
		"""
		INSERT ... INTO ...
		"""

		data = self.parse_body()

		self.get_request_table()

		try:
			self.table(**data).put()
		except:
			raise Error400

	@auth
	@catch_errors
	@common_headers
	def put(self):
		"""
		UPDATE ...
		"""

		data = self.parse_body()

		objects = self.get_filtered_objects()

		for obj in objects.fetch(objects.count()):
			for key, val in data.items():
				if key in obj._fields:
					obj.__setattr__(key, val)
					obj.put()
				else:
					raise Error400

	@auth
	@catch_errors
	@common_headers
	def delete(self):
		"""
		DELETE FROM ...
		"""

		objects = self.get_filtered_objects()

		for obj in objects.fetch(objects.count()):
			obj.delete()

	@catch_errors
	def parse_body(self):
		return json.loads(self.request.body)

	@catch_errors
	def get_request_table(self):
		table = None

		try:
			table = eval('models.' + self.request.path[1:].capitalize())
		except AttributeError:
			self.error(404)

		self.table = table
		return table

	@catch_errors
	def parse_request_filters(self):
		s_filters = self.request.get('filters')

		if not s_filters:
			raise Error400

		filters = []
		for s_filter in s_filters.split(':'):
			filters.append(s_filter.split(','))

		return filters

	@catch_errors
	def get_filtered_objects(self):
		self.get_request_table()
		table = self.table

		if 'filters' in self.request.arguments():
			filters = self.parse_request_filters()
		else:
			filters = []

		if filters:
			query = "WHERE "
		else:
			query = []

		query_params = []
		try:
			for filter_ in filters:
				if len(filter_) == 1:
					if filter_[0] not in ('NOT', 'AND', 'OR'):
						raise Error400
					else:
						query += ' %s ' % filter_[0]

				elif len(filter_) == 3:
					query += ' %s %s :%d ' % (filter_[0], filter_[1], len(query_params) + 1)

					param_type = eval('type(table.%s).data_type' % filter_[0])
					if param_type is basestring:
						param_type = str

					query_params.append(param_type(filter_[2]))

				else:
					raise Error400

		except:
			raise Error400

		if filters:
			return table.gql(query, *query_params)
		else:
			return table.all()


urlconf = {
	'/.*': RemoteSQLServer,
}

app = webapp2.WSGIApplication(urlconf.items(), debug=True)
