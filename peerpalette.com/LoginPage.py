from google.appengine.api import users
from google.appengine.ext import db

from gaesessions import get_current_session

import common
import models
from RequestHandler import RequestHandler

class LoginPage(RequestHandler):
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

      self.login_user(user.key(), True if self.request.get('rememberme') else False)
      self.redirect("/")
      return

    self.login()
    self.render_page('LoginPage.html')

  def post(self):
    username = self.request.get("username", None)
    password_hash = common.get_hash(self.request.get("password", ""))

    m = db.Query(models.Login).filter('username =', username).filter('password_hash =', password_hash).get()
    if m is None:
      self.login()
      self.template_values["login_username"] = username
      self.template_values["message"] = "Invalid username or password."
      self.render_page('LoginPage.html')
      return

    self.login_user(common.get_ref_key(m, 'user'), True if self.request.get('rememberme') else False)
    self.redirect("/")
    return

