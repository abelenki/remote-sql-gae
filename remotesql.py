# -*- encoding: utf-8 -*-

#  Copyright 2012 Artyom Maslovsky

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

__doc__ = """
This module contains the RemoteSQL server class that handles any request
to this application.
"""

import webapp2
import json
import cgi

import models


def auth(method):
    """
    Decorator for methods that require authorization
    """

    # Autorization token - when persists in a request's Cookie header,
    # it considered valid.
	AUTH_TOKEN = 'caf0ab246d8649580665683653f6825a'

	def wrapper(self, *pargs, **kwargs):

        # If 'auth' cookie exists, compare it's value with the authorization
        # token.
		if 'auth' in self.request.cookies:
			if self.request.cookies['auth'] == AUTH_TOKEN:

                # When they coinced call method
				return method(self, *pargs, **kwargs)

			else:
                # Otherwise show '401 Unathorized'
				self.error(401)

		else:
            # Otherwise show '401 Unauthorized'
			self.error(401)

	return wrapper



# Represents 'HTTP 400 Bad Request' error
class Error400: pass

def catch_errors(method):
    """
    Decorator for catching any error in method
    """

	def wrapper(self, *pargs, **kwargs):

		try:
            # Expect any error here
			return method(self, *pargs, **kwargs)

		except:
            # When exception appears, show '400 Bad Request'
			self.error(400)

	return wrapper

def common_headers(method):
    """
    Decorator for adding some common headers to method's response
    """

	def wrapper(self, *pargs, **kwargs):

        # NOTE: 'Connection' header is deprecated for GAE applications
		self.response.headers['Connection'] = 'close'

		self.response.headers['Content-Type'] = 'application/json'

		return method(self, *pargs, **kwargs)

	return wrapper


class RemoteSQLServer(webapp2.RequestHandler):
    """
    This class represents remote SQL server logic.
    Emulated SQL phrases (and corresponding methods):
        - get() -- SELECT ... FROM ...
        - post() -- INSERT INTO ...
        - put() -- UPDATE ...
        - delete() -- DELETE FROM ...
    """

	@auth
	@catch_errors
	@common_headers
	def get(self):
		"""
		SELECT ... FROM ...
		"""

        # Get filteres objects list
		objects = self.get_filtered_objects()

        # Compose result list
		result = []
		for obj in objects.fetch(objects.count()):

            # Represent each object as dictionary
			obj_dir = {}

            # Include all object's keys into response
			for key in obj._fields:
				if not key.startswith('_'):
					obj_dir[key] = obj.__getattribute__(key)

            # Put object into result list
			result.append(obj_dir)

        # Put the result list to the response as JSON byte string
		self.response.out.write(json.dumps(result))

	@auth
	@catch_errors
	@common_headers
	def post(self):
		"""
		INSERT ... INTO ...
		"""

        # Get sent data
		data = self.parse_body()

        # Get request table object
		self.get_request_table()

		try:
            # Trying to create new record in table
			self.table(**data).put()
		except:
            # If any error appears - Bad Request
			raise Error400

	@auth
	@catch_errors
	@common_headers
	def put(self):
		"""
		UPDATE ...
		"""

        # Get sent data
		data = self.parse_body()

        # Get filteres objects list
		objects = self.get_filtered_objects()

        # For each object change required attributes
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

        # Get filteres objects list
		objects = self.get_filtered_objects()

        # Delete every object
		for obj in objects.fetch(objects.count()):
			obj.delete()

	@catch_errors
	def parse_body(self):
        """
        Convert request body as JSON bytes string to Python object
        """
		return json.loads(self.request.body)

	@catch_errors
	def get_request_table(self):
        """
        Search for requested table
        """
		table = None

		try:
			table = eval('models.' + self.request.path[1:].capitalize())
		except AttributeError:
			self.error(404)

		self.table = table
		return table

	@catch_errors
	def parse_request_filters(self):
        """
        Convert filters url parameter to Python object
        """
		s_filters = self.request.get('filters')

		if not s_filters:
			raise Error400

		filters = []
		for s_filter in s_filters.split(':'):
			filters.append(s_filter.split(','))

		return filters

	@catch_errors
	def get_filtered_objects(self):
        """
        Create a list of filteres objects from request table
        """
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

        # Parsing filters and creating GQL query
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

        # Applying GQL to the table
		if filters:
			return table.gql(query, *query_params)
		else:
			return table.all()



# Application URL configuration
urlconf = {

	'/.*': RemoteSQLServer,

}

# Main application object
app = webapp2.WSGIApplication(urlconf.items(), debug=False)
