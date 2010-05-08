import httplib2
from os import remove
from patu import Patu, Spinner
import sys

TEST_URL = 'http://www.djangoproject.com'
SEEN_URLS = set(['http://www.djangoproject.com',
                 'http://www.djangoproject.com/',
                 'http://www.djangoproject.com/community/',
                 'http://www.djangoproject.com/download/',
                 'http://www.djangoproject.com/foundation/',
                 'http://www.djangoproject.com/weblog/',
                 'http://www.djangoproject.com/weblog/2010/apr/14/django-1_2-release-schedule-update-5/',
                 'http://www.djangoproject.com/weblog/2010/apr/22/django-1_2-release-schedule-update-6/',
                 'http://www.djangoproject.com/weblog/2010/apr/28/django-1_2-release-schedule-update-7/',
                 'http://www.djangoproject.com/weblog/2010/may/05/12-rc-1/'])

class MockHttpResponse(dict):
    def __init__(self, url, status=200, location=None):
        self.status = status
        self.location = location
        self['content-location'] = url

class MockHttp(httplib2.Http):
    def request(self, url):
        if url == TEST_URL:
            resp = MockHttpResponse(url)
            content = open('test_data/test.html').read()
        else:
            resp = MockHttpResponse(url)
            content = open('test_data/test.html').read()
        return resp, content

def test_parse_html():
    p = Patu(urls=[TEST_URL])
    r = p.get_urls(MockHttp(), TEST_URL)
    assert r.links == ['http://www.djangoproject.com/',
                       'http://www.djangoproject.com/',
                       'http://www.djangoproject.com/download/',
                       'http://www.djangoproject.com/weblog/',
                       'http://www.djangoproject.com/community/',
                       'http://www.djangoproject.com/download/',
                       'http://www.djangoproject.com/weblog/2010/may/05/12-rc-1/',
                       'http://www.djangoproject.com/weblog/2010/may/05/12-rc-1/',
                       'http://www.djangoproject.com/weblog/2010/apr/28/django-1_2-release-schedule-update-7/',
                       'http://www.djangoproject.com/weblog/2010/apr/28/django-1_2-release-schedule-update-7/',
                       'http://www.djangoproject.com/weblog/2010/apr/22/django-1_2-release-schedule-update-6/',
                       'http://www.djangoproject.com/weblog/2010/apr/22/django-1_2-release-schedule-update-6/',
                       'http://www.djangoproject.com/weblog/2010/apr/14/django-1_2-release-schedule-update-5/',
                       'http://www.djangoproject.com/weblog/2010/apr/14/django-1_2-release-schedule-update-5/',
                       'http://www.djangoproject.com/foundation/']

def test_spinner():
    s = Spinner()
    for x in xrange(0,6):
        s.spin()
    assert s.status == 2

def test_crawl():
    h = httplib2.Http
    httplib2.Http = MockHttp

    p = Patu(urls=[TEST_URL], depth=1)
    p.crawl()

    httplib2.Http = h
    assert p.seen_urls == SEEN_URLS

def test_generate():

    with open('test_data/test_generated.txt', 'w') as f:
        h = httplib2.Http
        httplib2.Http = MockHttp
        s = sys.stdout
        sys.stdout = f

        p = Patu(urls=[TEST_URL], depth=1, generate=True)
        p.crawl()

        sys.stdout = s
        httplib2.Http = h
    with open('test_data/test_generated.txt', 'r') as f:
        generated_urls = f.read().strip()
    remove('test_data/test_generated.txt')
    correct_urls = """
http://www.djangoproject.com	None
http://www.djangoproject.com/weblog/	http://www.djangoproject.com
http://www.djangoproject.com/weblog/2010/apr/22/django-1_2-release-schedule-update-6/	http://www.djangoproject.com
http://www.djangoproject.com/	http://www.djangoproject.com
http://www.djangoproject.com/weblog/2010/apr/28/django-1_2-release-schedule-update-7/	http://www.djangoproject.com
http://www.djangoproject.com/weblog/2010/may/05/12-rc-1/	http://www.djangoproject.com
http://www.djangoproject.com/weblog/2010/apr/14/django-1_2-release-schedule-update-5/	http://www.djangoproject.com
http://www.djangoproject.com/foundation/	http://www.djangoproject.com
http://www.djangoproject.com/community/	http://www.djangoproject.com
http://www.djangoproject.com/download/	http://www.djangoproject.com
"""
    correct_urls = correct_urls.strip()
    assert generated_urls == correct_urls

def test_stdin():
    with open('test_data/test_input.txt') as f:
        h = httplib2.Http
        httplib2.Http = MockHttp
        s = sys.stdin
        sys.stdin = f

        p = Patu(depth=1, input_file='-', verbose=True)
        p.crawl()

        sys.stdin = s
        httplib2.Http = h
    assert p.seen_urls == SEEN_URLS

def test_file_input():
    h = httplib2.Http
    httplib2.Http = MockHttp

    p = Patu(depth=1, input_file='test_data/test_input.txt')
    p.crawl()

    httplib2.Http = h
    assert p.seen_urls == SEEN_URLS

def test_no_http():
    h = httplib2.Http
    httplib2.Http = MockHttp

    p = Patu(urls=['www.djangoproject.com'], depth=1)
    p.crawl()

    httplib2.Http = h
    assert p.seen_urls == SEEN_URLS
