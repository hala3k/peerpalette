from google.appengine.ext import db

import config
import models
import common
from RequestHandler import RequestHandler

class InboxPage(RequestHandler):
  def get(self):
    self.init()
    convs_query = db.Query(models.UserChat).ancestor(self.user).order('-last_updated')
    cur = self.request.get('cursor')
    if cur:
      convs_query.with_cursor(start_cursor = cur)
      with_cursor = True
    else:
      with_cursor = False
    
    conversations = []
    peer_keys = []
    counter = 0
    cursor = None
    for conv in convs_query:
      if not conv.last_updated:
        continue
      counter += 1
      c = {'title' : conv.title, 'name' : conv.name}
      peer_key = common.get_ref_key(conv, 'peer_userchat').parent()
      c['username'] = models.User.get_username(peer_key)

      c['unread'] = True if self.is_unread(conv.key().id_or_name()) else False

      if conv.excerpt:
        c['excerpt'] = conv.excerpt

      conversations.append(c)
      peer_keys.append(peer_key)

      if counter >= config.ITEMS_PER_PAGE:
        cursor = convs_query.cursor()
        break

    peers_status = self.fetcher.get([db.Key.from_path('UserStatus', pk.id_or_name()) for pk in peer_keys])

    for i in range(len(conversations)):
      conv = conversations[i]
      idle_time = common.get_user_idle_time(peers_status[i])
      status_class = common.get_status_class(idle_time)
      conv['status_class'] = status_class

    self.template_values["conversations"] = conversations
    self.template_values["cursor"] = cursor
    self.template_values["with_cursor"] = with_cursor

    self.render_page('InboxPage.html')

