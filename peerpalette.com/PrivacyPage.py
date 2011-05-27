from RequestHandler import RequestHandler

class PrivacyPage(RequestHandler):
  def get(self):
    self.login()
    self.render_page('PrivacyPage.html')

