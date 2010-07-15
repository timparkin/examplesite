"""
Simple script to index a database using the joecornish.lib.index module.
"""

import logging
import sys
import couchdb
import twitter
import feedparser
import couchdb
from examplesite.lib import html2text
from datetime import datetime
import time

import adminish, couchish
from adminish import index


def main(db_url):
    db = couchdb.Database(db_url)
    twitter_posts = get_twitter_posts()
    blog_posts = get_blog_posts()
    socialmedia = db['socialmedia']
    socialmedia.update({'twitter': twitter_posts, 'blog': blog_posts})
    db.update([socialmedia])

def get_twitter_posts():
    api = twitter.Api()
    data = api.GetUserTimeline('charlottebritto')
    posts = []
    for d in data:
        created_at_datetime = datetime.fromtimestamp(d.created_at_in_seconds)
        posts.append({
             'text': d.text,
             'relative_created_at': d.relative_created_at,
             'created_at_datetime': created_at_datetime.isoformat()
                    })
    return posts[:3]

def get_blog_posts():
    data = feedparser.parse("http://www.charlottebritton.co.uk/feeds/posts/default")
    posts = []
    for d in data['entries']:
        published = datetime.fromtimestamp(time.mktime(d['published_parsed']))
        posts.append({
            'title': d.title,
            'summary': html2text.html2text(d['subtitle']),
            'published': published.isoformat(),
            'link': d['link']
        })
    return posts[:3]






if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    db_url = sys.argv[1]
    main(db_url)

