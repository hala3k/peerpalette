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
from UpdateQueriesAgeIndex import UpdateQueriesAgeIndex
from CleanupOnlineUsers import CleanupOnlineUsers
from LoginPage import LoginPage
from LogoutPage import LogoutPage
import Ajax

application = webapp.WSGIApplication(
                                     [('/', HomePage),
                                      ('/privacy', PrivacyPage),
                                      ('/feedback', FeedbackPage),
                                      ('/search', SearchPage),
                                      ('/startchat', StartChatPage),
                                      ('/sendmessage', Ajax.SendMessage),
                                      ('/receivemessages', Ajax.ReceiveMessages),
                                      ('/getunread', Ajax.GetUnread),
                                      ('/inbox', InboxPage),
                                      ('/history', HistoryPage),
                                      ('/update_queries_age_index/([012])', UpdateQueriesAgeIndex),
                                      ('/cleanup_online_users', CleanupOnlineUsers),
                                      ('/random', RandomChat),
                                      ('/login', LoginPage),
                                      ('/logout', LogoutPage),
                                      ('/chat/(.*)', ChatPage)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
