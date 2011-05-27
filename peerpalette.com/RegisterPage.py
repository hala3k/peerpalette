from google.appengine.api import users
from google.appengine.ext import db
from gaesessions import get_current_session

import common
import models
from RequestHandler import RequestHandler

import re

# source: http://code.activestate.com/recipes/65215-e-mail-address-validation/
def validate_email(email):
	if len(email) > 7:
		if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
			return True
	return False

def get_email_username(email):
  if email:
    return email.split('@')[0]
  return None

class RegisterPage(RequestHandler):
  def get(self):
    self.login()
    link_type = self.request.get("link_type", None)
    if link_type == "google":
      google_user = users.get_current_user()
      if google_user is None:
        self.redirect(users.create_login_url("/register?link_type=google"))
        return
      self.template_values["login_username"] = get_email_username(google_user.nickname())
      if validate_email(google_user.email()):
        self.template_values["email"] = google_user.email()

    self.template_values["link_type"] = link_type
    self.render_page("RegisterPage.html")

  def post(self):
    username = self.request.get("username", None)
    password = self.request.get("password", None)
    verify_password = self.request.get("verify_password", None)
    link_type = self.request.get("link_type", None)
    email = self.request.get("email", None)

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
    elif email and not validate_email(email):
      error_message = "Email is invalid." 

    if error_message:
      self.login()
      self.template_values["login_username"] = username
      self.template_values["message"] = error_message
      self.template_values["link_type"] = link_type

      self.render_page("RegisterPage.html")
      return

    password_hash = common.get_hash(password)
    user = models.User(key_name = username)
    user.put()
    login = models.Login(user = user, username = username, password_hash = password_hash)
    if validate_email(email):
      login.email = email
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

