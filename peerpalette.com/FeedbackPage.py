from google.appengine.api import mail

from RequestHandler import RequestHandler

import os
import datetime

class FeedbackPage(RequestHandler):
  def get(self):
    self.login()
    self.render_page('FeedbackPage.html')

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

    self.login()
    self.template_values['submitted'] = True
    self.render_page('FeedbackPage.html')

