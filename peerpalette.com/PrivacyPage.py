from RequestHandler import RequestHandler

class PrivacyPage(RequestHandler):
  def get(self):
    self.init()
    self.render_page('PrivacyPage.html')

