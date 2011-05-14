from google.appengine.api import users
from google.appengine.ext import db
from gaesessions import get_current_session

import common
import models
from RequestHandler import RequestHandler

import re

class RegisterPage(RequestHandler):
  def get(self):
    link_type = self.request.get("link_type", None)
    if link_type == "google":
      google_user = users.get_current_user()
      if google_user is None:
        self.redirect(users.create_login_url("/register?link_type=google"))
        return

    self.init()
    self.template_values["link_type"] = link_type
    self.render_page("RegisterPage.html")

  def post(self):
    username = self.request.get("username", None)
    password = self.request.get("password", None)
    verify_password = self.request.get("verify_password", None)
    link_type = self.request.get("link_type", None)

    google_user = None
    if link_type == "google":
      google_user = users.get_current_user()
      if google_user is None:
        self.redirect(users.create_login_url("/register?link_type=google"))
        return

    error_message = None

    m = db.Query(models.Login).filter('username =', username).get()

    if m is not None:
      error_message = "Username is taken. Please choose another one."
    elif not re.match("^[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)*$", username):
      error_message = "Invalid username. Please choose another one."
    elif len(username) < 6 or len(username) > 20:
      error_message = "Username should be between 6 and 20 characters long."
    elif password != verify_password:
      error_message = "Passwords do not match"
    elif not password:
      error_message = "Password can not be empty."
    elif not username:
      error_message = "Please enter your desired username."

    if error_message:
      self.init()
      self.template_values["login_username"] = username
      self.template_values["message"] = error_message
      self.template_values["link_type"] = link_type

      self.render_page("RegisterPage.html")
      return

    password_hash = common.get_hash(password)
    user = models.User(key_name = username)
    user.put()
    login = models.Login(user = user, username = username, password_hash = password_hash)
    login.put()

    if google_user:
      # delete existing login
      existing = db.Query(models.GoogleLogin).filter("google_user =", google_user).get()
      if existing is not None:
        existing.delete()

      google_login = models.GoogleLogin(google_user = google_user, user = user)
      google_login.put()

    get_current_session()["user"] = user.key()
    self.redirect("/")

