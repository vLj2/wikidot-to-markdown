#!/usr/bin/env python
# https://github.com/maxcutler/python-wordpress-xmlrpc

from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import GetRecentPosts, NewPost
from wordpress_xmlrpc.methods.users import GetUserInfo

import datetime as dt

SITE = 'http://blog.philippklaus.de/xmlrpc.php'
USER = 'pklaus'

password = raw_input('Please enter the password for the user %s: ' % USER)

wp = Client(SITE, USER, password)
#wp.call(GetRecentPosts(10))
#wp.call(GetUserInfo())

post = WordPressPost()
post.title = 'My new title'
post.description = 'This is the body of my new post.'
post.tags = 'automatically posted, datetime' # 'test, firstpost'
post.date_created = dt.datetime(2010, 9, 14, 11, 11, 11)
post.post_status = 'private'
post.categories = ['Computing']
wp.call(NewPost(post, True))



