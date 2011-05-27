from google.appengine.ext import db

import config
import models
import common
from RequestHandler import RequestHandler

class InboxPage(RequestHandler):
  def get(self):
    self.login()
    convs_query = db.Query(models.UserChat).ancestor(self.user_key).order('-last_updated')
    cur = self.request.get('cursor')
    if cur:
      convs_query.with_cursor(start_cursor = cur)
      with_cursor = True
    else:
      with_cursor = False
    
    conversations = []
    users_status = []
    unread_chats = []
    counter = 0
    cursor = None
    for conv in convs_query:
      if not conv.last_updated:
        continue
      counter += 1
      c = {'title' : conv.title, 'name' : conv.name}
      peer_key = common.get_ref_key(conv, 'peer_userchat').parent()
      c['username'] = models.User.get_username(peer_key)

      conversations.append(c)
      unread_chats.append(self.datastore_fetcher.get(db.Key.from_path('User', self.user_key.id_or_name(), 'UnreadChat', conv.key().id_or_name())))
      users_status.append(self.memcache_fetcher.get(config.MEMCACHE_LAST_BEEN_ONLINE(peer_key.id_or_name())))

      if counter >= config.ITEMS_PER_PAGE:
        cursor = convs_query.cursor()
        break

    for i in range(len(conversations)):
      conv = conversations[i]
      status_class = "online" if users_status[i].get_result() is not None else "offline"
      conv['status_class'] = status_class
      conv['unread'] = False if unread_chats[i].get_result() is None else True

    self.template_values["conversations"] = conversations
    self.template_values["cursor"] = cursor
    self.template_values["with_cursor"] = with_cursor

    self.render_page('InboxPage.html')

