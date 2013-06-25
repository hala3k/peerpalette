import webapp2


# Pages
from HomePage import HomePage
from SearchPage import SearchPage
from ChatPage import ChatPage
from ChatPage import StartChatPage
from ChatPage import LoadMoreMessages
from InboxPage import InboxPage
from HistoryPage import HistoryPage
from RandomChat import RandomChat
from PrivacyPage import PrivacyPage
from FeedbackPage import FeedbackPage
from CleanupOnlineUsers import CleanupOnlineUsers
from CleanupTopSearches import CleanupTopSearches
from LoginPage import LoginPage
from LogoutPage import LogoutPage
from RegisterPage import RegisterPage
from SettingsPage import SettingsPage
import Ajax

app = webapp2.WSGIApplication([
                                      ('/', HomePage),
                                      ('/privacy', PrivacyPage),
                                      ('/feedback', FeedbackPage),
                                      ('/search', SearchPage),
                                      ('/startchat', StartChatPage),
                                      ('/getupdate', Ajax.GetUpdate),
                                      ('/getchatupdate', Ajax.GetUpdate),
                                      ('/sendmessage', Ajax.GetUpdate),
                                      ('/updatecontext', Ajax.UpdateContext),
                                      ('/load_more_messages', LoadMoreMessages),
                                      ('/chats', InboxPage),
                                      ('/topics', HistoryPage),
                                      ('/cleanup_online_users', CleanupOnlineUsers),
                                      ('/cleanup_top_searches', CleanupTopSearches),
                                      ('/random', RandomChat),
                                      ('/login', LoginPage),
                                      ('/register', RegisterPage),
                                      ('/logout', LogoutPage),
                                      ('/chat/(.*)', ChatPage),
                                      ('/settings', SettingsPage),
                                     ], debug=True)
