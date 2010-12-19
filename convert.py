#!/usr/bin/env python

## for string.join()
import string

import sys

## for os.makedirs()
import os

## for optparse.OptionParser()
import optparse

import re

import markdown

## for codecs.open()
import codecs

## to generate random UUIDs using uuid.uuid4()
import uuid

# https://github.com/maxcutler/python-wordpress-xmlrpc
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import GetRecentPosts, NewPost
from wordpress_xmlrpc.methods.users import GetUserInfo

# for dt.datetime() and dt.datetime.now()
import datetime as dt

## for time.sleep()
import time

#SITE = 'http://blog.philippklaus.de/xmlrpc.php'
SITE = 'http://pklaus.wordpress.com/xmlrpc.php'
USER = 'pklaus'
DEFAULT_OUTPUT_DIR = "output"
SLEEP_TIME = 1 # seconds to sleep after each post sent to the blog (if you use your own server, set this to 0)

class WikidotToMarkdown(object):
    def __init__(self):
        # regex for URL found on http://regexlib.com/REDetails.aspx?regex_id=501
        self.url_regex = r"(http|https|ftp)\://([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&amp;%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.(com|edu|gov|int|mil|net|org|biz|arpa|info|name|pro|aero|coop|museum|[a-zA-Z]{2}))(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&amp;%\$#\=~_\-]+))*[/]?"

        self.static_replacements = { '[[toc]]': '', # no equivalent for table of contents in Markdown
                                   }
        self.regex_replacements = { r'^\+ ([^\n]*)$': r"# \1\n", # headings
                                     r'^\+\+ ([^\n]*)$': r"## \1\n",
                                     r'^\+\+\+ ([^\n]*)$': r"### \1\n",
                                     r'([^:])//([\s\S ]*?)//': r'\1*\2*',
                                   }
        self.regex_split_condition = r"^\+ ([^\n]*)$"
    
    def convert(self, text):
        # first we search for [[code]] statements as we do not any replacement to happen inside those code blocks!
        code_blocks = dict()
        code_blocks_found = re.findall(re.compile(r'(\[\[code( type="([\S]+)")?\]\]([\s\S ]*?)\[\[/code\]\])',re.MULTILINE), text)
        for code_block_found in code_blocks_found:
            tmp_hash = str(uuid.uuid4())
            text = text.replace(code_block_found[0],tmp_hash,1) # replace code block with a hash - to fill it in later
            code_blocks[tmp_hash] = "\n"+string.join(["    " + l for l in code_block_found[-1].strip().split("\n") ],"\n")+"\n"
        for search, replacement in self.static_replacements.items():
            text = text.replace(search,replacement,1)
        # search for any of the simpler replacements in the dictionary regex_replacements
        for s_reg, r_reg in self.regex_replacements.items():
            text = re.sub(re.compile(s_reg,re.MULTILINE),r_reg,text)
        # search for simple http://www.google.com links:
        for link in re.finditer(r"[\s\S\n ]("+self.url_regex+r")", text):
            if link.group(0)[0] == "[" : continue
            text = text.replace(link.group(1),"<%s>  " % link.group(1),1)
        # search for links of the form [http://www.google.com Google Website]
        for link in re.finditer(r"\[("+self.url_regex+r") ([^\]]*)\]", text):
            #print link.group(0), "[%s](%s)" % (link.groups()[-1],link.group(1))
            text = text.replace(link.group(0),"[%s](%s)" % (link.groups()[-1],link.group(1)),1)
	# search for unhandled tags and state them
        for unhandled_tag in re.finditer(r"\[\[/([\s\S ]*?)\]\]", text):
            print("Found an unhandled tag: %s" % unhandled_tag.group(1))
        # now we substitute back our code blocks
        for tmp_hash, code in code_blocks.items():
            text = text.replace(tmp_hash, code, 1)
        return text

    def split_text(self, text):
        output_parts = []
        split_regex = re.compile(self.regex_split_condition) 
        for line in text.split("\n"):
            line += "\n"
            if len(output_parts) > 0 and (re.match(split_regex,line) == None): output_parts[-1] += line
            else: output_parts.append(line)
        return output_parts
            
class ConversionController(object):
    """"""
    
    def __init__(self, options):
        """constructor
        """
        self.__input_wiki_file = options.filename
        self.__output_directory = options.output_dir
        self.__fill_blog = options.blog
        self.__create_individual_files = options.individual

        self.__converter = WikidotToMarkdown()

    def __prepare_output_dir(self):
        #os.makedirs(self.__output_directory) ## to see the exception do not put it inside a try..except
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
                print("\nAttention! We skip the first output part:\n\n%s" % text_part)
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
        #wp.call(GetRecentPosts(10))
        #wp.call(GetUserInfo())

    def post_new(self, title, content, categories = ['Computing'], individual_tags = '', status = 'private', date = dt.datetime.now()):
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
    p.add_option('--fill-blog', '-b', action="store_true", help="fill the blog", default=False, dest="blog")
    p.add_option('--save-individual', '-s', action="store_true", help="save individual files for every headline", default=False, dest="individual")
    p.add_option('--input-file', '-f', metavar="INPUT_FILE", help="Read from INPUT_FILE.", dest="filename")
    p.add_option('--output-dir', '-o', metavar="OUTPUT_DIRECTORY", help="Save the converted files to the OUTPUT_DIRECTORY.", dest="output_dir")
    
    # parse our CLI options
    options, arguments = p.parse_args()
    if options.filename == None:
        p.error("Please provide the filename to convert as the first argument!")
        sys.exit(1)
    if options.output_dir == None:
        options.output_dir = raw_input('Please enter an output directory for the converted documents [%s]: ' % DEFAULT_OUTPUT_DIR)
        if options.output_dir == "": options.output_dir = DEFAULT_OUTPUT_DIR

    converter = ConversionController(options)
    converter.convert()

if __name__ == '__main__':
    main()


