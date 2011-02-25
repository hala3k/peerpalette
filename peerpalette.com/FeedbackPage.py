from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import mail

import config
import common
import os

class FeedbackPage(webapp.RequestHandler):
  def get(self):
    user = common.get_current_user_info()

    template_values = {
      "unread_count" : user._unread_count,
      "unread_alert" : True if len(user._new_chats) > 0 else False,
      "timestamp" : user._new_timestamp,
    }

    path = os.path.join(os.path.dirname(__file__), 'FeedbackPage.html')
    self.response.out.write(template.render(path, template_values))

  def post(self):
    message = self.request.get("message")
    sender = self.request.get("email", "noreply.peerpalette.com")
    if not message or not sender:
      self.redirect("/feedback")
      return

    subject = message[:30]

    mail.send_mail(sender = sender,
              to = "Zaid Abdulla <zkam83+peerpalette@gmail.com>",
              subject = subject,
              body= message)

    user = common.get_current_user_info()

    template_values = {
      "unread_count" : user._unread_count,
      "unread_alert" : True if len(user._new_chats) > 0 else False,
      "timestamp" : user._new_timestamp,
      "submitted" : True,
    }

    path = os.path.join(os.path.dirname(__file__), 'FeedbackPage.html')
    self.response.out.write(template.render(path, template_values))

