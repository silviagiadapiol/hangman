"""user_class.py - This file contains the Game class and its forms
   definitions"""

from protorpc import messages
from google.appengine.ext import ndb


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    victories = ndb.IntegerProperty(default=0)
    losses = ndb.IntegerProperty(default=0)
    ratio = ndb.FloatProperty(default=0.0)

    def to_form(self):
        form = UserForm()
        form.name = self.name
        form.email = self.email
        form.ratio = self.ratio
        form.victories = self.victories
        form.losses = self.losses
        return form


class UserForm(messages.Message):
    """UserForm for outbound ranking"""
    name = messages.StringField(1, required=True)
    email = messages.StringField(2)
    ratio = messages.FloatField(3)
    victories = messages.IntegerField(4)
    losses = messages.IntegerField(5)


class UserForms(messages.Message):
    """Return multiple UserForms"""
    items = messages.MessageField(UserForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
