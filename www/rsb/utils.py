import re
import datetime
import requests
import simplejson as json
import feedparser
from time import mktime

from django.core.cache import cache


def fetch_tweets(username='codeinthehole'):
    """
    Return tweets but with caching
    """
    key = 'tweets_%s' % username
    tweets = cache.get(key)
    if tweets is None:
        try:
            tweets = _fetch_tweets(username)
        except Exception:
            tweets = []
        else:
            cache.set(key, tweets, 300)
    return tweets


def _fetch_tweets(username='codeinthehole'):
    """
    Return a list of tweets for a given user
    """
    url = "https://twitter.com/statuses/user_timeline.json?screen_name=%s" % username
    response = requests.get(url)
    raw_tweets = json.loads(response.content)
    if 'error' in raw_tweets:
        return []
    processed_tweets = []
    for tweet in raw_tweets:
        # Ignore replies
        if tweet['text'].startswith('@'):
            continue
        data = {
            'text': htmlify(tweet['text']),
            'date_created': datetime.datetime.strptime(tweet['created_at'], "%a %b %d %H:%M:%S +0000 %Y")}
        processed_tweets.append(data)
    return processed_tweets


urlfinder = re.compile(r"(https?://[^ ]+)")
tweeterfinder = re.compile(r"@(\w+)")
hashtagfinder = re.compile(r"#(\w+)")


def anchorise_urls(text):
    return urlfinder.sub(r'<a href="\1">\1</a>', text)


def anchorise_twitter_user_refs(text):
    return tweeterfinder.sub(r'<a href="http://twitter.com/\1">@\1</a>', text)

def anchorise_twitter_hashtags(text):
    return hashtagfinder.sub(r'<a href="http://twitter.com/#!/search/%23\1">#\1</a>', text)
    

def htmlify(text):
    filters = [anchorise_urls,
               anchorise_twitter_user_refs,
               anchorise_twitter_hashtags]
    output = text
    for fn in filters:
        output = fn(output)
    return output


def fetch_github_activity(username='codeinthehole'):
    key = 'github_%s' % username
    activity = cache.get(key)
    if activity is None:
        activity = _fetch_github_activity(username)
        cache.set(key, activity, 3600)
    return activity

def _fetch_github_activity(username):
    url = 'https://github.com/%s.atom' % username
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries:
        timestamp = mktime(entry['updated_parsed'])
        item = {'date_updated': datetime.datetime.fromtimestamp(timestamp),
                'summary': anchorise_github_links(entry['summary'])}
        items.append(item)
    return items

linkfinder = re.compile(r"\"/")

def anchorise_github_links(text):
    return linkfinder.sub(r'"https://github.com/', text)