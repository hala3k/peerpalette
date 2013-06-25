import webapp2
from google.appengine.ext import webapp
from google.appengine.api import users

from gaesessions import get_current_session

class LogoutPage(webapp2.RequestHandler):
  def get(self):
    get_current_session().pop("user")
    self.redirect("/")

