from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.webapp import template

import os

from gaesessions import get_current_session

import common
import models

class LoginPage(webapp.RequestHandler):
  def get(self):
    login_type = self.request.get("login_type", None)
    if login_type == "google":
      google_user = users.get_current_user()
      if google_user is None:
        self.redirect(users.create_login_url("/login?login_type=google"))
        return

      google_login = db.Query(models.GoogleLogin).filter("google_user =", google_user).get()
      if google_login:
        user = google_login.user
      else:
        self.redirect("/register?link_type=google")
        return

      get_current_session()["user"] = str(user.key())
      self.redirect("/")
      return

    user = common.get_current_user_info()

    template_values = {
      "unread_count" : user._unread_count,
      "unread_alert" : True if len(user._new_chats) > 0 else False,
      "timestamp" : user._new_timestamp,
      "username" : user.username(),
      "anonymous" : user.anonymous(),
    }
    path = os.path.join(os.path.dirname(__file__), 'LoginPage.html')
    self.response.out.write(template.render(path, template_values))

  def post(self):
    username = self.request.get("username", None)
    password_hash = common.get_hash(self.request.get("password", ""))

    m = db.Query(models.Login).filter('username =', username).filter('password_hash =', password_hash).get()
    if m is None:
      user = common.get_current_user_info()

      template_values = {
        "unread_count" : user._unread_count,
        "unread_alert" : True if len(user._new_chats) > 0 else False,
        "timestamp" : user._new_timestamp,
        "username" : user.username(),
        "anonymous" : user.anonymous(),
        "username" : user.username(),
        "login_username" : username,
        "message" : "Invalid username or password.",
      }
      path = os.path.join(os.path.dirname(__file__), 'LoginPage.html')
      self.response.out.write(template.render(path, template_values))
      return

    get_current_session()["user"] = common.get_ref_key(m, 'user')
    self.redirect("/")
    return
    


