#!/usr/bin/env python
# https://github.com/maxcutler/python-wordpress-xmlrpc

from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import GetRecentPosts, NewPost
from wordpress_xmlrpc.methods.users import GetUserInfo

SITE = 'http://blog.philippklaus.de/xmlrpc.php'
USER = 'pklaus'

password = raw_input('Please enter the password for the user %s: ' % USER)

wp = Client(SITE, USER, password)
#wp.call(GetRecentPosts(10))
#wp.call(GetUserInfo())

post = WordPressPost()
post.title = 'My new title'
post.description = 'This is the body of my new post.'
post.tags = 'Ubuntu GNU/Linux, automatically posted' # 'test, firstpost'
post.post_status = 'private'
post.categories = ['Computing']
wp.call(NewPost(post, True))



