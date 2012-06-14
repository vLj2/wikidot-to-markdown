#!/usr/bin/env python
# -*- encoding: UTF8 -*-

# Copyright 2012 Philipp Klaus
# Part of https://github.com/vLj2/wikidot-to-markdown

import re ## The most important module here!
import string ## for string.join()
#import markdown
import uuid ## to generate random UUIDs using uuid.uuid4()

class WikidotToMarkdown(object):
    def __init__(self):
        # regex for URL found on http://regexlib.com/REDetails.aspx?regex_id=501
        self.url_regex = r"(http|https|ftp)\://([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&amp;%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.(com|edu|gov|int|mil|net|org|biz|arpa|info|name|pro|aero|coop|museum|[a-zA-Z]{2}))(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&amp;%\$#\=~_\-]+))*[/]?"

        self.static_replacements = { '[[toc]]': '', # no equivalent for table of contents in Markdown
                                   }
        self.regex_replacements = { r'^\+ ([^\n]*)$': r"# \1\n", # headings
                                    r'^\+\+ ([^\n]*)$': r"## \1\n",
                                    r'^\+\+\+ ([^\n]*)$': r"### \1\n",
                                    r'([^:])//([\s\S ]*?)//': r'\1*\2*', # italics
                                    r'([^:])__([\s\S ]*?)__': r'\1**\2**', # underlining → bold
                                    r'([^:]){{([\s\S ]*?)}}': r'\1`\2`', # inline monospaced text
                                  }
        self.regex_split_condition = r"^\+ ([^\n]*)$"

    def convert(self, text):
        text = '\n'+text+'\n'# add embed in newlines (makes regex replaces work better)
        # first we search for [[code]] statements as we don't want any replacement to happen inside those code blocks!
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
        return text[1:-1]

    def split_text(self, text):
        output_parts = []
        split_regex = re.compile(self.regex_split_condition)
        for line in text.split("\n"):
            line += "\n"
            if len(output_parts) > 0 and (re.match(split_regex,line) == None): output_parts[-1] += line
            else: output_parts.append(line)
        return output_parts
