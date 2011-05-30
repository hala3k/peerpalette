from RequestHandler import RequestHandler
from google.appengine.ext import db

import models

class SettingsPage(RequestHandler):
  def get(self):
    self.login()
    linked_accounts = db.Query(models.GoogleLogin).filter('user =', self.user_key).fetch(10)
    self.template_values['linked_accounts'] = [a.google_user.email() for a in linked_accounts]
    self.render_page('SettingsPage.html')
  def post(self):
    self.login()
    if self.request.get('action') == 'Delete Account':
      if self.request.get('delete_account'):
        from utils import delete_user
        from urllib import urlencode
        delete_user(self.user_key.id_or_name())
        self.session.terminate()
        self.redirect('/?%s' % urlencode({'notify' : 'Account deleted'}))
        return
      else:
        self.action_feedback.append({'class' : 'error', 'message' : 'Please verify that you want to delete this account by ticking the checkbox'})
    elif self.request.get('action') == 'Unlink Account':
      from google.appengine.api.users import User
      accounts = self.request.get_all('linked_account')
      todel = []
      for acc in accounts:
        todel.append(db.Query(models.GoogleLogin, keys_only=True).filter('user =', self.user_key).filter('google_user =', User(acc)).get())
        self.action_feedback.append({'class' : 'notify', 'message' : 'Unlinked %s' % acc})
      db.delete(todel)
    elif self.request.get('action') == 'Change Password':
      from common import get_hash
      current_password_hash = get_hash(self.request.get('current_password', ''))
      new_password_hash = get_hash(self.request.get('new_password', ''))
      verify_new_password_hash = get_hash(self.request.get('verify_new_password', ''))

      login = db.Query(models.Login).filter('username =', self.user_key.name()).filter('password_hash =', current_password_hash).get()
      if login is None:
        self.action_feedback.append({'class' : 'error', 'message' : 'Wrong password'})
      elif new_password_hash != verify_new_password_hash:
        self.action_feedback.append({'class' : 'error', 'message' : 'Provided passwords don\' match'})
      else:
        login.password_hash = new_password_hash
        login.put()
        self.action_feedback.append({'class' : 'notify', 'message' : 'Password changed'})

    linked_accounts = db.Query(models.GoogleLogin).filter('user =', self.user_key).fetch(10)
    self.template_values['linked_accounts'] = [a.google_user.email() for a in linked_accounts]
    self.render_page('SettingsPage.html')
