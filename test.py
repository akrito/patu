from os import remove
from patu import Patu, Spinner

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

class MockHttplib2(object):
    class Http(object):
        def __init__(self, *args, **kwargs):
            pass

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
    r = p.get_urls(MockHttplib2.Http(), TEST_URL)
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
    p = Patu(urls=[TEST_URL], httplib=MockHttplib2, depth=1)
    p.crawl()
    assert p.seen_urls == SEEN_URLS

def test_generate():
    with open('test_data/test_generated.txt', 'w') as f:
        p = Patu(urls=[TEST_URL], httplib=MockHttplib2, depth=1, generate=True, stdout=f)
        p.crawl()
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
        p = Patu(httplib=MockHttplib2, depth=1, input_file='-', stdin=f, verbose=True)
        p.crawl()
    assert p.seen_urls == SEEN_URLS

def test_file_input():
    p = Patu(httplib=MockHttplib2, depth=1, input_file='test_data/test_input.txt')
    p.crawl()
    assert p.seen_urls == SEEN_URLS

def test_no_http():
    p = Patu(urls=['www.djangoproject.com'], httplib=MockHttplib2, depth=1)
    p.crawl()
    assert p.seen_urls == SEEN_URLS
