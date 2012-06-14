#!/usr/bin/env python

# Copyright 2012 Philipp Klaus
# Part of https://github.com/vLj2/wikidot-to-markdown

from wikidot import WikidotToMarkdown ## most important here

import sys ## for sys.exit()
import os ## for os.makedirs()
import optparse ## for optparse.OptionParser()
import markdown ## for markdown.markdown()
import codecs ## for codecs.open()
import datetime as dt # for dt.datetime() and dt.datetime.now()
import time ## for time.sleep()

# https://github.com/maxcutler/python-wordpress-xmlrpc
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost
from wordpress_xmlrpc.methods.users import GetUserInfo

SITE = 'http://blog.example.com/xmlrpc.php'
#SITE = 'http://yourblog.wordpress.com/xmlrpc.php'
USER = 'username'
DEFAULT_OUTPUT_DIR = "output"
#SLEEP_TIME = 1 # seconds to sleep after each post sent to the blog (if you use your own server, set this to 0)
SLEEP_TIME = 0

class ConversionController(object):
    def __init__(self, options):
        self.__input_wiki_file = options.filename
        self.__output_directory = options.output_dir
        self.__fill_blog = options.blog
        self.__create_individual_files = options.individual
        self.__converter = WikidotToMarkdown()

    def __prepare_output_dir(self):
        try:
            os.makedirs(self.__output_directory)
        except OSError as ex:
            print("Could not create output folder "+self.__output_directory+".")
            if ex.errno == os.errno.EEXIST: print("It already exists.")
            else: print "Error %i: %s" % (ex.errno, str(ex)); sys.exit(1)

    def convert(self):
        self.__prepare_output_dir()
        f = codecs.open(self.__input_wiki_file, encoding='utf-8')
        text = f.read()

        # write the complete files to the output directory:
        complete_text = self.__converter.convert(text)
        self.write_unicode_file("%s/%s" % (self.__output_directory, 'complete.mktxt'),complete_text)
        html_text = '<html><head><title>%s</title><style type="text/css">%s</style></head><body><div class="wikistyle">' % ('Converted Markdown',file('style.css').read())
        html_text += markdown.markdown(complete_text)
        html_text += "</div></body></html>"
        self.write_unicode_file("%s/%s" % (self.__output_directory, 'complete.html'),html_text)

        # now handle the texts split to little junks:
        if self.__create_individual_files:
            parts = self.__converter.split_text(text)
            if len(parts) < 2: return # we need at least 2 entries (the first part is trashed and one part with content!)
            i=0
            if self.__fill_blog:
                wprb = WordPressPostingRobot(SITE,USER)
                start_day = raw_input('Please enter the start date for the posts: [%s] ' % dt.datetime.now().strftime("%Y-%m-%d") )
                start_day = start_day if start_day != "" else dt.datetime.now().strftime("%Y-%m-%d")
                start = [int(value) for value in start_day.split("-")]
                end_day = raw_input('Please enter the end date for the posts: [%s] ' % dt.datetime.now().strftime("%Y-%m-%d") )
                end_day = end_day if end_day != "" else dt.datetime.now().strftime("%Y-%m-%d")
                end = [int(value) for value in end_day.split("-")]
                days_difference = (dt.datetime(end[0],end[1],end[2])-dt.datetime(start[0],start[1],start[2])).days
                gradient = .0 if len(parts) == 2 else float(days_difference)/(len(parts)-2)
            for text_part in parts:
                text_part =  self.__converter.convert(text_part)
                i += 1
                if i == 1:
                    print("\nAttention! We skip the first output part (when splitting the text into parts):\n\n%s" % text_part)
                    continue
                if self.__create_individual_files: self.write_unicode_file("%s/%i%s" % (self.__output_directory, i, '.mktxt'),text_part)
                lines = text_part.split("\n")
                if self.__fill_blog:
                    title = lines[0].replace("# ","")
                    content = string.join(lines[1:],'\n')
                    date = dt.datetime(start[0],start[1],start[2], 17, 11, 11) + dt.timedelta(int((i-2)*gradient))
                    wprb.post_new(title, content,[],'','private',date)
                    time.sleep(SLEEP_TIME)

    def write_unicode_file(self, path_to_file, content):
        try:
            out_file = codecs.open(path_to_file,encoding='utf-8', mode='w')
            out_file.write(content)
        except:
            print "Error on writing to file %s." % path_to_file


class WordPressPostingRobot(object):
    def __init__(self, site, user, password=""):
        if password == "": password = raw_input('Please enter the password for the user %s: ' % user)
        self.additional_tags = raw_input('Please enter additional tags to give to all the posts: ')
        self.__wp = Client(site, user, password)
        #wp.call(GetUserInfo())

    def post_new(self, title, content, categories = ['Mac OS X'], individual_tags = '', status = 'private', date = dt.datetime.now()):
        post = WordPressPost()
        post.title = title
        post.description = content
        tags = 'automatically posted' if (self.additional_tags == '')  else self.additional_tags + ', automatically posted'
        tags = individual_tags + tags
        post.tags = tags
        post.date_created = date
        post.post_status = status
        post.categories = categories
        self.__wp.call(NewPost(post, True))


def main():
    """ Main function called to start the conversion."""
    p = optparse.OptionParser(version="%prog 1.0")

    # set possible CLI options
    p.add_option('--save-junks-to-blog', '-b', action="store_true", help="save the individual files as blog posts (only relevant if -s set)", default=False, dest="blog")
    p.add_option('--save-individual', '-s', action="store_true", help="save individual files for every headline", default=False, dest="individual")
    p.add_option('--input-file', '-f', metavar="INPUT_FILE", help="Read from INPUT_FILE.", dest="filename")
    p.add_option('--output-dir', '-o', metavar="OUTPUT_DIRECTORY", help="Save the converted files to the OUTPUT_DIRECTORY.", dest="output_dir")

    # parse our CLI options
    options, arguments = p.parse_args()
    if options.filename == None:
        p.error("No filename for the input file set. Have a look at the parameters using the option -h.")
        sys.exit(1)
    if options.output_dir == None:
        options.output_dir = raw_input('Please enter an output directory for the converted documents [%s]: ' % DEFAULT_OUTPUT_DIR)
        if options.output_dir == "": options.output_dir = DEFAULT_OUTPUT_DIR

    converter = ConversionController(options)
    converter.convert()

if __name__ == '__main__':
    main()
