#!/usr/bin/env python
# coding: utf-8


import json
from NoPS import NoPS
import unittest


class TestNoPS(unittest.TestCase):

    def test__normalize_space(self):
        nops = NoPS()
        self.assertEqual('t e s t', nops._normalize_space(' t e  s   t   '))

    def test__tokenize_url(self):
        nops = NoPS()
        self.assertEqual('a b c', nops._tokenize_url("a/b/c"))
        self.assertEqual('d e f ', nops._tokenize_url("http://d/e/f/"))

    def test_case(self):
        nops = NoPS()
        nops.feed('<HTML><Body>')
        self.assertEqual(['html', 'body'], nops.tag_stack)

    def test_tag_counting(self):
        nops = NoPS()
        nops.feed('<html><body><div><div>')
        self.assertEqual({'html': 1, 'body': 1, 'div': 2}, nops.tag_count)
        nops.feed('</span>')
        self.assertEqual({'html': 1, 'body': 1, 'div': 2}, nops.tag_count)
        nops.feed('</body>')
        self.assertEqual({'html': 1, 'body': 0, 'div': 0}, nops.tag_count)

    def test_tag_stacking(self):
        nops = NoPS()
        self.assertEqual([], nops.tag_stack)
        nops.feed('<html><body><div><div>')
        self.assertEqual(['html', 'body', 'div', 'div'], nops.tag_stack)
        nops.feed('</div>')
        self.assertEqual(['html', 'body', 'div'], nops.tag_stack)
        nops.feed('</body>')  # should also closes the first div
        self.assertEqual(['html'], nops.tag_stack)

    def test_in_title(self):
        nops = NoPS()
        self.assertEqual(False, nops.in_title)
        nops.feed('<html><head><title>')
        self.assertEqual(True, nops.in_title)
        nops.feed('</title>')
        self.assertEqual(False, nops.in_title)
        nops.feed('<title>')
        self.assertEqual(False, nops.in_title)  # ignores multiple titles

        nops = NoPS()
        self.assertEqual(False, nops.in_title)
        nops.feed('<html><head><title>')
        self.assertEqual(True, nops.in_title)
        nops.feed('</head>')  # also closes the title
        self.assertEqual(False, nops.in_title)

    def test_no_title(self):
        nops = NoPS()
        self.assertEqual(False, nops.in_title)
        self.assertEqual(None, nops.title)
        nops.feed('<html><head></head></html>')
        self.assertEqual(False, nops.in_title)
        self.assertEqual(None, nops.title)

    def test_title(self):
        nops = NoPS()
        self.assertEqual(None, nops.title)
        nops.feed('<html><title>t1</title></html>')
        self.assertEqual('t1', nops.title)

    def test_multiple_titles(self):
        nops = NoPS()
        self.assertEqual(None, nops.title)
        nops.feed('<html><title>t1</title><title>t2</title></html>')
        self.assertEqual('t1', nops.title)  # ignore multiple titles

    def test_empty_title(self):
        nops = NoPS()
        self.assertEqual(None, nops.title)
        nops.feed('<html><title></html>')
        self.assertEqual('', nops.title)

    def test_no_base(self):
        nops = NoPS()
        self.assertEqual(False, nops.seen_base)
        self.assertEqual(None, nops.base_href)
        nops.feed('<html><head></head></html>')
        self.assertEqual(False, nops.seen_base)
        self.assertEqual(None, nops.base_href)

    def test_base(self):
        nops = NoPS()
        self.assertEqual(False, nops.seen_base)
        self.assertEqual(None, nops.base_href)
        nops.feed('<html><head><base href="value"></head></html>')
        self.assertEqual(True, nops.seen_base)
        self.assertEqual('value', nops.base_href)

    def test_multiple_bases(self):
        nops = NoPS()
        self.assertEqual(None, nops.base_href)
        nops.feed('<html><head><base><base href="value"></head></html>')
        self.assertEqual(None, nops.base_href)  # ignore multiple bases

    def test_base_no_href(self):
        nops = NoPS()
        self.assertEqual(False, nops.seen_base)
        self.assertEqual(None, nops.base_href)
        nops.feed('<html><head><base></head></html>')
        self.assertEqual(True, nops.seen_base)
        self.assertEqual(None, nops.base_href)

    def test_ignore_by(self):
        nops = NoPS()
        self.assertEqual(None, nops.ignore_by)
        nops.feed('<html><head><script>')
        self.assertEqual(3, nops.ignore_by)
        nops.feed('</script>')
        self.assertEqual(None, nops.ignore_by)
        nops.feed('<style>')
        self.assertEqual(3, nops.ignore_by)
        nops.feed('</style>')
        self.assertEqual(None, nops.ignore_by)

        nops = NoPS()
        self.assertEqual(None, nops.ignore_by)
        nops.feed('<html><body><iframe>')
        self.assertEqual(3, nops.ignore_by)
        nops.feed('</body>')
        self.assertEqual(None, nops.ignore_by)

        nops = NoPS()
        self.assertEqual(None, nops.ignore_by)
        nops.feed('<html><body><iframe><iframe>')
        self.assertEqual(3, nops.ignore_by)
        nops.feed('</iframe>')
        self.assertEqual(3, nops.ignore_by)
        nops.feed('</iframe>')
        self.assertEqual(None, nops.ignore_by)

    def test_ignorance(self):
        nops = NoPS()
        nops.feed('a<noscript>b<noscript>c</noscript>d</noscript>e')
        self.assertEqual(' a e', nops.content_string)

    def test_content_string(self):
        nops = NoPS()
        self.assertEqual('', nops.content_string)
        nops.feed('<html><body> Test  ')
        self.assertEqual(' Test', nops.content_string)
        nops.feed('<div>   document    </div>')
        self.assertEqual(' Test document', nops.content_string)

    def test_img(self):
        nops = NoPS()
        nops.EXTRACT_TEXT_OF_IMG = False
        nops.feed('<img>')
        self.assertEqual(' <IMG:no-src>', nops.content_string)

        nops = NoPS()
        nops.EXTRACT_TEXT_OF_IMG = False
        nops.feed('<img src="画像.jpg">')
        self.assertEqual(' <IMG:%E7%94%BB%E5%83%8F.jpg>',
                         nops.content_string)

    def test_stringify_img(self):
        nops = NoPS()
        nops.feed('<img>')
        self.assertEqual('', nops.content_string)
        nops.feed('<img src="a/b/c">')
        self.assertEqual(' a b c', nops.content_string)
        nops.feed('<img src="http://d/e/f">')
        self.assertEqual(' a b c d e f', nops.content_string)

        nops = NoPS()
        nops.feed('<img>')
        nops.feed('<img alt="t e  s   t    ">')
        self.assertEqual(' t e s t', nops.content_string)

        nops = NoPS()
        nops.feed('<img>')
        nops.feed('<img src="a/b/c" alt="t e  s   t    ">')
        self.assertEqual(' a b c t e s t', nops.content_string)

    def test_dumps(self):
        nops = NoPS()
        jstr = nops.dumps('http://test')
        jobj = json.loads(jstr)
        self.assertEqual([{
            'from': 5,
            'to': 5,
            'mandatory': True,
        }], jobj['contents'])
        self.assertEqual([], jobj['children'])

        nops = NoPS()
        nops.feed(' Content  body.   ')
        jstr = nops.dumps('http://test')
        jobj = json.loads(jstr)
        self.assertEqual([{
            'from': 5,
            'to': 18,
            'mandatory': True,
        }], jobj['contents'])
        self.assertEqual(nops.content_string, ' Content body.')

    def test_extract_url(self):
        nops = NoPS()
        jstr = nops.dumps('http://test')
        jobj = json.loads(jstr)
        self.assertEqual('http://test', jobj['URL'])
        self.assertEqual('http://test', jobj['baseURL'])

        nops = NoPS()
        nops.feed('<base href="http://base">')
        jstr = nops.dumps('http://test')
        jobj = json.loads(jstr)
        self.assertEqual('http://test', jobj['URL'])
        self.assertEqual('http://base', jobj['baseURL'])

        nops = NoPS()
        nops.EXTRACT_URL = False
        jstr = nops.dumps('http://test')
        jobj = json.loads(jstr)
        self.assertFalse('URL' in jobj)
        self.assertFalse('baseURL' in jobj)

    def test_extract_title(self):
        nops = NoPS()
        nops.feed('<title> Test  Title   </title>')
        jstr = nops.dumps('http://test')
        jobj = json.loads(jstr)
        self.assertEqual('Test Title', jobj['rawString'])
        self.assertEqual([[{
            'from': 0,
            'to': 10,
            'mandatory': True,
        }]], jobj['headings'])

    def test_extract_url(self):
        nops = NoPS()
        jstr = nops.dumps('http://a/b/c')
        jobj = json.loads(jstr)
        self.assertEqual('a b c', jobj['rawString'])
        self.assertEqual([[{
            'from': 0,
            'to': 5,
            'mandatory': True,
        }]], jobj['headings'])

    def test_extract_url_with_base(self):
        nops = NoPS()
        nops.feed('<base href="http://test">')
        jstr = nops.dumps('http://dummy')
        jobj = json.loads(jstr)
        self.assertEqual('test', jobj['rawString'])
        self.assertEqual([[{
            'from': 0,
            'to': 4,
            'mandatory': True,
        }]], jobj['headings'])

        nops = NoPS()
        nops.feed('<base href="http://test/">')
        jstr = nops.dumps('http://path')
        jobj = json.loads(jstr)
        self.assertEqual('test path', jobj['rawString'])
        self.assertEqual([[{
            'from': 0,
            'to': 9,
            'mandatory': True,
        }]], jobj['headings'])

    def test_extract_no_page_heading(self):
        nops = NoPS()
        nops.EXTRACT_PAGE_HEADING = False
        jstr = nops.dumps('http://dummy')
        jobj = json.loads(jstr)
        self.assertEqual('', jobj['rawString'])
        self.assertEqual([], jobj['headings'])
        self.assertEqual([{
            'from': 1,
            'to': 1,
            'mandatory': True,
        }], jobj['contents'])

        nops = NoPS()
        nops.EXTRACT_PAGE_HEADING = False
        nops.feed(' Content  body.   ')
        jstr = nops.dumps('http://dummy')
        jobj = json.loads(jstr)
        self.assertEqual(' Content body.', jobj['rawString'])
        self.assertEqual([], jobj['headings'])
        self.assertEqual([{
            'from': 1,
            'to': 14,
            'mandatory': True,
        }], jobj['contents'])
