from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

import config
import common
import os

class PrivacyPage(webapp.RequestHandler):
  def get(self):
    user = common.get_current_user_info()

    template_values = {
      "unread_count" : user._unread_count,
      "unread_alert" : True if len(user._new_chats) > 0 else False,
      "timestamp" : user._new_timestamp,
    }

    path = os.path.join(os.path.dirname(__file__), 'PrivacyPage.html')
    self.response.out.write(template.render(path, template_values))
