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
        delete_user(self.user_key.id_or_name())
        self.session.terminate()
        self.redirect('/')
        return
    elif self.request.get('action') == 'Unlink Account':
      # delete google login
      pass
    elif self.request.get('action') == 'Change Password':
      pass

    linked_accounts = db.Query(models.GoogleLogin).filter('user =', self.user_key).fetch(10)
    self.template_values['linked_accounts'] = [a.google_user.email() for a in linked_accounts]
    self.render_page('SettingsPage.html')
