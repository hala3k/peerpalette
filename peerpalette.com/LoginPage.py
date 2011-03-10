from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext import db

from gaesessions import get_current_session

import common
import models

class LoginPage(webapp.RequestHandler):
  def get(self):
    login_type = self.request.get("type", None)
    if login_type == "google":
      google_user = users.get_current_user()
      if google_user is None:
        self.redirect("/login")
        return
      google_login = db.Query(models.GoogleLogin).filter("google_user =", google_user).get()
      if google_login:
        user = google_login.user
      else:
        user = models.User(username = google_user.nickname())
        user.put()
        google_login = models.GoogleLogin(google_user = google_user, user = user)
        google_login.put()
        
      get_current_session()["user"] = str(user.key())
      self.redirect("/")
      return
    self.redirect(users.create_login_url("/login?type=google"))

