from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
import common
import os

class HomePage(webapp.RequestHandler):
  def get(self):
    user = common.get_user()
    template_values = {
      "unread_html" : common.get_unread_count_html(user)
    }
    path = os.path.join(os.path.dirname(__file__), 'HomePage.html')
    self.response.out.write(template.render(path, template_values))
