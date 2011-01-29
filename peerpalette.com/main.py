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
import QueriesRating
import Ajax

application = webapp.WSGIApplication(
                                     [('/', HomePage),
                                      ('/search', SearchPage),
                                      ('/startchat', StartChatPage),
                                      ('/sendmessage', Ajax.SendMessage),
                                      ('/receivemessages', Ajax.ReceiveMessages),
                                      ('/getunread', Ajax.GetUnread),
                                      ('/inbox', InboxPage),
                                      ('/history', HistoryPage),
                                      ('/update_user_queries_rating', QueriesRating.UpdateUserQueriesRating),
                                      ('/update_queries_rating/([01])', QueriesRating.UpdateQueriesRating),
                                      ('/random', RandomChat),
                                      ('/chat/(.*)', ChatPage)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
