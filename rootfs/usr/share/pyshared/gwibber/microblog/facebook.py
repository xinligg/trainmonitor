#!/usr/bin/env python

import network, util
from util import exceptions, log
import hashlib, mx.DateTime, time
from os.path import join, getmtime, exists
from gettext import lgettext as _
from util.const import *
# Try to import * from custom, install custom.py to include packaging 
# customizations like distro API keys, etc
try:
  from util.custom import *
except:
  pass

log.logger.name = "Facebook"

PROTOCOL_INFO = {
  "name": "Facebook",
  "version": "1.0",
  
  "config": [
    "color",
    "receive_enabled",
    "send_enabled",
    "username",
    "session_key",
    "private:secret_key"
  ],

  "authtype": "facebook",
  "color": "#64006C",

  "features": [
    "send",
    "reply",
    "receive",
    "responses",
    "thread",
    "delete",
    "send_thread",
    "like",
    "lists",
    "list",
    "sincetime"
  ],

  "default_streams": [
    "receive",
    "responses",
    "images",
    "lists",
  ]
}

URL_PREFIX = "https://api.facebook.com/restserver.php"
POST_URL = "http://www.facebook.com/profile.php?id=%s&v=feed&story_fbid=%s&ref=mf"

class Client:
  def __init__(self, acct):
    self.account = acct
    self.user_id = acct["session_key"].split("-")[1]

  def _check_error(self, data):
    if isinstance(data, dict) and "error_code" in data:
      log.logger.info("Facebook error %s - %s", data["error_code"], data["error_msg"])
      return True
    else: 
      return False
    
  def _get(self, operation, post=False, single=False, **args):
    args.update({
      "v": "1.0",
      "format": "json",
      "method": "facebook." + operation,
      "api_key": FB_APP_KEY,
      "session_key": self.account["session_key"],
      "call_id": str(int(time.time()) * 1000),
    })

    sig = "".join("%s=%s" % (k, v) for k, v in sorted(args.items()))
    args["sig"] = hashlib.md5(sig + self.account["secret_key"]).hexdigest()
    data = network.Download(URL_PREFIX, args, post).get_json()

    if isinstance(data, dict) and data.get("error_msg", 0):
      if "permission" in data["error_msg"]:
        raise exceptions.GwibberServiceError("auth", self.account["service"], self.account["username"], data["error_msg"])

    return data

  def _sender(self, user):
    sender = {
      "name": user["name"],
      "id": str(user["id"]),
      "is_me": str(user["id"]) == self.user_id,
      "url": user["url"],
      "image": user["pic_square"],
    }
    
    if user["url"] and not "?" in user["url"]:
      sender["nick"] = user["url"].rsplit("/", 1)[-1]
    return sender
  
  def _message(self, data, profiles):
    m = {}
    m["mid"] = str(data["post_id"])
    m["service"] = "facebook"
    m["account"] = self.account["id"]
    m["time"] = int(mx.DateTime.DateTimeFrom(int(data['created_time'])).gmtime())
    m["url"] = data["permalink"]

    if data.get("attribution", 0):
      m["source"] = util.strip_urls(data["attribution"]).replace("via ", "")
    
    if data.get("message", "").strip():
      m["text"] = data["message"]
      m["html"] = util.linkify(data["message"])
      m["content"] = m["html"]
    else:
      m["text"] = ""
      m["html"] = ""
      m["content"] = ""

    if data.get("actor_id", 0) in profiles:
      m["sender"] = self._sender(profiles[data["actor_id"]])

    if data.get("likes", {}).get("count", None):
      m["likes"] = {
        "count": data["likes"]["count"],
        "url": data["likes"]["href"],
      }

    if data.get("comments", 0):
      m["comments"] = []
      for item in data["comments"]["comment_list"]:
        if item["fromid"] in profiles:
          m["comments"].append({
            "text": item["text"],
            "time": int(mx.DateTime.DateTimeFrom(int(item["time"])).gmtime()),
            "sender": self._sender(profiles[item["fromid"]]),
          })

    if data.get("attachment", 0):
      if data["attachment"].get("name", 0):
        m["content"] += "<p><b>%s</b></p>" % data["attachment"]["name"]

      if data["attachment"].get("description", 0):
        m["content"] += "<p>%s</p>" % data["attachment"]["description"]

      m["images"] = []
      for a in data["attachment"].get("media", []):
        if a["type"] in ["photo", "video", "link"]:
          if a.get("src", 0):
            if a["src"].startswith("/"):
              a["src"] = "http://facebook.com" + a["src"]
            m["images"].append({"src": a["src"], "url": a["href"]})

    return m

  def _comment(self, data, profiles):
    user = profiles[data["fromid"]]
    return {
      "mid": str(data["id"]),
      "service": "facebook",
      "account": self.account["id"],
      "time": int(mx.DateTime.DateTimeFrom(int(data['time'])).gmtime()),
      "text": "@%s: %s" % (self.account["username"], data["text"]),
      "content": "@%s: %s" % (self.account["username"], data["text"]),
      "html": "@%s: %s" % (self.account["username"], data["text"]),
      "reply": {
        "id": data["post_id"],
        "nick": self.account["username"],
        "url": POST_URL % (self.user_id, data["object_id"]),
      },
      "sender": {
        "nick": user["username"] or str(user["uid"]),
        "name": user["name"],
        "id": str(user["uid"]),
        "url": user["profile_url"],
        "image": user["pic_square"],
      }
    }

  def _image(self, data, profiles):
    user = profiles[data["owner"]]
    return {
      "mid": str(data["object_id"]),
      "service": "facebook",
      "account": self.account["id"],
      "time": int(mx.DateTime.DateTimeFrom(int(data['created'])).gmtime()),
      "content": data["caption"],
      "text": data["caption"],
      "html": data["caption"],
      "images": [{
        "full": data["src_big"],
        "src": data["src_big"],
        "thumb": data["src_small"],
        "url": data["link"],
      }],
      "sender": {
        "nick": user["username"] or str(user["uid"]),
        "name": user["name"],
        "id": str(user["uid"]),
        "url": user["profile_url"],
        "image": user["pic_square"],
      }
    }

  def _list(self, data, user):
    return {
        "mid": data["value"],
        "service": "facebook",
        "account": self.account["id"],
        "time": 0,
        "text": "",
        "html": "",
        "content": "",
        "url": "#", # http://www.facebook.com/friends/?filter=flp_%s" % data["flid"],
        "name": data["name"],
        "nick": data["name"],
        "key": data["filter_key"],
        "full": "",
        "type": data["type"],
        "kind": "list",
        "fbstreamicon": data["icon_url"],
        "sender": {
          "nick": user["username"] or str(user["uid"]),
          "name": user["name"],
          "id": str(user["uid"]),
          "url": user["profile_url"],
          "image": user["pic_square"],
        }
    }

  def _friends(self):
    friends_cache_file = join(CACHE_DIR, ("%s_friends.cache" % self.account["id"]))
    if not exists(friends_cache_file):
      f = file(friends_cache_file, "w")
      f.close()
    f = open(friends_cache_file, "r")
    try:
      friends = eval(f.read())
    except SyntaxError:
      friends = ""
    if (int(getmtime(friends_cache_file)) < int(mx.DateTime.DateTimeFromTicks(mx.DateTime.localtime()) - mx.DateTime.TimeDelta(hours=4.0))) \
      or not isinstance(friends, list):
      log.logger.debug("facebook:friends is refreshing at %s", mx.DateTime.localtime())
      
      f.close()
      f = open(friends_cache_file, "r+")
      friends = self._get("fql.query", query="""
        SELECT name, profile_url, pic_square, username, uid
          FROM user WHERE uid in (SELECT uid2 FROM friend WHERE uid1=%s)
        """ % self.user_id)
      f.write(str(friends))
      f.close()
      log.logger.debug("<STATS> facebook:friends account:%s size:%s", self.account["id"], str(friends).__len__())

    if not self._check_error(friends):
      return dict((p["uid"], p) for p in friends)
    else:
      return

  def __call__(self, opname, **args):
    return getattr(self, opname)(**args)

  def thread(self, id):
    query = "SELECT name, profile_url, pic_square, username, uid FROM user WHERE uid in \
      (SELECT fromid FROM comment WHERE post_id = '%s')" % id
    
    profiles = dict((p["uid"], p) for p in self._get("fql.query", query=query))
    comments = self._get("stream.getComments", post_id=id)
    return [self._comment(comment, profiles) for comment in comments]

  def receive(self, since=None):
    if not since:
      since = int(mx.DateTime.DateTimeFromTicks(mx.DateTime.localtime()) - mx.DateTime.TimeDelta(hours=240.0))

    data = self._get("stream.get", viewer_id=self.user_id, start_time=since, limit=80)
    
    log.logger.debug("<STATS> facebook:receive account:%s since:%s size:%s",
        self.account["id"], mx.DateTime.DateTimeFromTicks(since), len(str(data)))
    
    if not self._check_error(data):
      profiles = dict((p["id"], p) for p in data["profiles"])
      return [self._message(post, profiles) for post in data["posts"]]
    else: return

  def responses(self, since=None, limit=100):
    if not since:
      since = int(mx.DateTime.DateTimeFromTicks(mx.DateTime.localtime()) - mx.DateTime.TimeDelta(hours=240.0))

    data = self._get("fql.query", query="""
      SELECT id, post_id, time, fromid, text, object_id FROM comment WHERE post_id IN
        (SELECT post_id FROM stream WHERE source_id = %s) AND
        fromid <> %s 
        AND time > %s
        ORDER BY time DESC LIMIT %s
      """ % (self.user_id, self.user_id, since, limit))

    log.logger.debug("<STATS> facebook:responses account:%s since:%s size:%s",
        self.account["id"], mx.DateTime.DateTimeFromTicks(since), len(str(data)))

    if not self._check_error(data):
      profiles = self._friends()
      return [self._comment(comment, profiles) for comment in data]
    else: return 

  def lists(self, **args):
    data = self._get("fql.query", query="""
      SELECT name, profile_url, pic_square, username, uid
        FROM user WHERE uid=%s""" % self.user_id)
    if not self._check_error(data):
      user = data[0]
    else: return

    return [self._list(l, user) for l in self._get("Stream.getFilters")]

  def list(self, user, id, count=util.COUNT, since=None):
    if not since:
      since = int(mx.DateTime.DateTimeFromTicks(mx.DateTime.localtime()) - mx.DateTime.TimeDelta(hours=240.0))

    data = self._get("Stream.get", viewer_id=self.user_id, start_time=since, limit=80, filter_key=id)
    profiles = dict((p["id"], p) for p in data["profiles"])
    return [self._message(post, profiles) for post in data["posts"]]

  def images(self, limit=100, since=None):
    if not since:
      since = int(mx.DateTime.DateTimeFromTicks(mx.DateTime.localtime()) - mx.DateTime.TimeDelta(hours=240.0))

    data = self._get("fql.query", query="""
      SELECT owner, object_id, created, src_small, src_big, link, caption
        FROM photo WHERE aid in
        (SELECT aid FROM album WHERE owner IN
        (SELECT uid2 FROM friend WHERE uid1=%s))
        AND created > %s
        ORDER BY created DESC LIMIT %s
      """ % (self.user_id, since, limit))

    log.logger.debug("<STATS> facebook:images account:%s since:%s size:%s",
        self.account["id"], mx.DateTime.DateTimeFromTicks(since), len(str(data)))

    if not self._check_error(data):
      profiles = self._friends()
      return [self._image(post, profiles) for post in data if post["owner"] in profiles]
    else: return

  def delete(self, message):
    self._get("stream.remove", post_id=message["mid"])
    return []

  def like(self, message):
    self._get("stream.addLike", post_id=message["mid"])
    return []

  def send(self, message):
    self._get("users.setStatus", status=message, status_includes_verb=False)
    return []

  def send_thread(self, message, target):
    self._get("stream.addComment", post_id=target["mid"], comment=message)
    return []

