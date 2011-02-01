from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

import config
import common
import os

class PrivacyPage(webapp.RequestHandler):
  def get(self):
    user = common.get_user()

    unread = common.get_unread(user)

    template_values = {
      "unread_count" : unread[0],
      "unread_alert" : unread[1],
    }

    path = os.path.join(os.path.dirname(__file__), 'PrivacyPage.html')
    self.response.out.write(template.render(path, template_values))
