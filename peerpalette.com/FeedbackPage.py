from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import mail

import config
import common
import os

class FeedbackPage(webapp.RequestHandler):
  def get(self):
    user = common.get_user()

    unread = common.get_unread(user)

    template_values = {
      "unread_count" : unread[0],
      "unread_alert" : unread[1],
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

    user = common.get_user()
    unread = common.get_unread(user)

    template_values = {
      "submitted" : True,
      "unread_count" : unread[0],
      "unread_alert" : unread[1],
    }

    path = os.path.join(os.path.dirname(__file__), 'FeedbackPage.html')
    self.response.out.write(template.render(path, template_values))

