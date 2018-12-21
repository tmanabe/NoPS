#!/usr/bin/env python
# coding: utf-8


from html.parser import HTMLParser
from json import dumps
import re
import urllib


class Range(dict):
    FROM, TO = 'from', 'to'
    MANDATORY = 'mandatory'


class HeadingStructure(dict):
    CHILDREN = 'children'
    CONTENTS = 'contents'
    HEADINGS = 'headings'
    RAW_STRING = 'rawString'
    _URL, BASE_URL = 'URL', 'baseURL'


class NoPS(HTMLParser):

    IGNORE = {'iframe', 'noscript', 'script', 'style'}

    def __init__(self):
        super().__init__()
        self.tag_count = {}
        self.tag_stack = []
        self.in_title = False
        self.title = None
        self.seen_base = False
        self.base_href = None
        self.ignore_by = None  # th tag in tag_stack
        self.content_string = ''
        self.EXTRACT_URL = True
        self.EXTRACT_PAGE_HEADING = True
        self.EXTRACT_TEXT_OF_IMG = True

    def _normalize_space(self, string):
        string = re.sub(r'\s+', ' ', string)
        return string.strip()

    def _tokenize_url(self, string):
        string = string.rsplit('://', 1)[-1]
        return ' '.join(re.split(r'\W+', string))

    def handle_starttag(self, tag, attrs):
        if tag in self.tag_count:
            self.tag_count[tag] += 1
        else:
            self.tag_count[tag] = 1
        self.tag_stack.append(tag)
        if self.ignore_by is None and tag in self.IGNORE:
            self.ignore_by = len(self.tag_stack)
        elif tag == 'title' and self.title is None:
            self.in_title = True
            self.title = ''
        elif tag == 'base':
            if self.seen_base is False:
                self.seen_base = True
                attrs = dict(attrs)
                if 'href' in attrs and attrs['href'] is not None:
                    self.base_href = attrs['href']
        elif tag == 'img':
            attrs = dict(attrs)
            if self.EXTRACT_TEXT_OF_IMG:
                string = ''
                if 'src' in attrs and attrs['src'] is not None:
                    string += self._tokenize_url(attrs['src'])
                string += ' '
                if 'alt' in attrs and attrs['alt'] is not None:
                    string += attrs['alt']
                string = self._normalize_space(string)
                if string != '':
                    self.content_string += ' ' + string
            else:
                src = 'no-src'
                if 'src' in attrs:
                    src = attrs['src']
                    src = urllib.parse.quote(src, safe='~()*!.\'')
                self.content_string += ' <IMG:%s>' % src

    def handle_endtag(self, tag):
        last_tag = None
        if tag not in self.tag_count or self.tag_count[tag] < 1:
            return  # ignore the endtag
        while 0 < len(self.tag_stack) and last_tag != tag:
            if self.ignore_by == len(self.tag_stack):
                self.ignore_by = None
            last_tag = self.tag_stack.pop()
            self.tag_count[last_tag] -= 1
            if last_tag == 'title':
                self.in_title = False
        if tag == 'title':
            self.in_title = False
            if self.title is None:
                self.title = ''

    def handle_data(self, data):
        if self.ignore_by is not None:
            return
        if self.in_title:
            self.in_title = False
            self.title += data
        else:
            data = self._normalize_space(data)
            if data != '':
                self.content_string += ' ' + self._normalize_space(data)

    def dumps(self, url):
        hs = HeadingStructure()
        hs[HeadingStructure.HEADINGS] = []
        hs[HeadingStructure.CONTENTS] = []
        hs[HeadingStructure.CHILDREN] = []
        hs[HeadingStructure.RAW_STRING] = ''
        if self.EXTRACT_URL:
            hs['URL'] = url
            hs['baseURL'] = self.base_href or url
        heading_to = 0
        if self.EXTRACT_PAGE_HEADING:
            if self.title is not None:
                self.title = self._normalize_space(self.title)
                hs[HeadingStructure.RAW_STRING] += self.title
            else:
                merged_url = ''
                if self.base_href is not None:
                    merged_url = self.base_href
                    if merged_url[-1] == '/':
                        merged_url += url.rsplit('/')[-1]
                else:
                    merged_url = url
                merged_url = self._tokenize_url(merged_url)
                merged_url = self._normalize_space(merged_url)
                hs[HeadingStructure.RAW_STRING] += merged_url
            h = []
            heading_to = len(hs[HeadingStructure.RAW_STRING])
            r = Range()
            r.update({
                Range.FROM: 0,
                Range.TO: heading_to,
                Range.MANDATORY: True,
            })
            h.append(r)
            hs[HeadingStructure.HEADINGS].append(h)
        hs[HeadingStructure.RAW_STRING] += self.content_string
        contents_to = len(hs[HeadingStructure.RAW_STRING])
        r = Range()
        r.update({
            Range.FROM: heading_to + 1,
            Range.TO: max(heading_to + 1, contents_to),
            Range.MANDATORY: True,
        })
        hs[HeadingStructure.CONTENTS].append(r)
        return dumps(hs)
