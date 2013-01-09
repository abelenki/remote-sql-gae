from google.appengine.ext import db

class People(db.Model):
	name = db.StringProperty(default="")
	email = db.StringProperty(required=True)
	grade = db.IntegerProperty(default=0)
	info = db.TextProperty(default="")

	_fields = ['name', 'email', 'grade', 'info']
