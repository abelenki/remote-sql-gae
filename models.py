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

from google.appengine.ext import db

class People(db.Model):
    """
    'People' table, fields:
        - varchar name
        - varchar email
        - int grade
        - text info
    """
    name = db.StringProperty(default="")
    email = db.StringProperty(required=True)
    grade = db.IntegerProperty(default=0)
    info = db.TextProperty(default="")

    _fields = ['name', 'email', 'grade', 'info']
