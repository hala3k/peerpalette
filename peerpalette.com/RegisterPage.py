from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.webapp import template

import os

from gaesessions import get_current_session

import common
import models
import hashlib

class RegisterPage(webapp.RequestHandler):
  def get(self):
    link_type = self.request.get("link_type", None)
    if link_type == "google":
      google_user = users.get_current_user()
      if google_user is None:
        self.redirect(users.create_login_url("/register?link_type=google"))
        return

    user = common.get_current_user_info()

    template_values = {
      "unread_count" : user._unread_count,
      "unread_alert" : True if len(user._new_chats) > 0 else False,
      "timestamp" : user._new_timestamp,
      "username" : user.username(),
      "anonymous" : user.anonymous(),
      "link_type" : link_type,
    }
    path = os.path.join(os.path.dirname(__file__), 'RegisterPage.html')
    self.response.out.write(template.render(path, template_values))

  def post(self):
    username = self.request.get("username", None).strip()
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

    if not password:
      error_message = "Password can not be empty."

    if password != verify_password:
      error_message = "Passwords do not match"

    if m is not None:
      error_message = "Username is taken. Please choose another one."

    if not username:
      error_message = "Please enter your desired username."

    if error_message:
      user = common.get_current_user_info()
      template_values = {
        "unread_count" : user._unread_count,
        "unread_alert" : True if len(user._new_chats) > 0 else False,
        "timestamp" : user._new_timestamp,
        "username" : user.username(),
        "anonymous" : user.anonymous(),
        "username" : user.username(),
        "login_username" : username,
        "message" : error_message,
        "link_type" : link_type,
      }
      path = os.path.join(os.path.dirname(__file__), 'RegisterPage.html')
      self.response.out.write(template.render(path, template_values))
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

    get_current_session()["user"] = str(user.key())
    self.redirect("/")

