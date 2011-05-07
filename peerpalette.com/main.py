from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

# Pages
from HomePage import HomePage
from SearchPage import SearchPage
from ChatPage import ChatPage
from ChatPage import StartChatPage
from InboxPage import InboxPage
from HistoryPage import HistoryPage
from RandomChat import RandomChat
from PrivacyPage import PrivacyPage
from FeedbackPage import FeedbackPage
from CleanupOnlineUsers import CleanupOnlineUsers
from LoginPage import LoginPage
from LogoutPage import LogoutPage
from RegisterPage import RegisterPage
import Ajax

application = webapp.WSGIApplication([
                                      ('/', HomePage),
                                      ('/privacy', PrivacyPage),
                                      ('/feedback', FeedbackPage),
                                      ('/search', SearchPage),
                                      ('/startchat', StartChatPage),
                                      ('/getupdate', Ajax.GetUpdate),
                                      ('/updatecontext', Ajax.UpdateContext),
                                      ('/inbox', InboxPage),
                                      ('/history', HistoryPage),
                                      ('/cleanup_online_users', CleanupOnlineUsers),
                                      ('/random', RandomChat),
                                      ('/login', LoginPage),
                                      ('/register', RegisterPage),
                                      ('/logout', LogoutPage),
                                      ('/chat/(.*)', ChatPage),
                                     ], debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
