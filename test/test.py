import httplib2
from nose.tools import eq_, with_setup
from os import path, remove
import sys

try:
    __file__
except NameError:
    __file__ = 'test/test.py'
sys.path.append(path.join(path.dirname(__file__), '..'))

from patu import Patu, Spinner, main

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
TEST_HTML = path.join(path.dirname(__file__), 'test.html')
TEST_INPUT = path.join(path.dirname(__file__), 'test_input.txt')
LINKS = ['http://www.djangoproject.com/',
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

class MockHttpResponse(dict):
    def __init__(self, url, status = 200, **kwargs):
        for key, value in kwargs:
            setattr(self, key, value)
        self.status = status
        self['content-location'] = url

class MockHttp(httplib2.Http):
    h = httplib2.Http
    def request(self, url):
        if url == 'http://redirect.me':
            resp = MockHttpResponse(url = 'http://www.djangoproject.com')
            content = open(TEST_HTML).read()
        elif url == 'http://djangoproject.com':
            resp = MockHttpResponse(url = 'http://www.djangoproject.com')
            content = open(TEST_HTML).read()
        elif url == 'http://error.me':
            resp = MockHttpResponse(url, status=500)
            content = ''
        elif url == 'http://keyboard.me':
            raise KeyboardInterrupt
        elif url == 'http://io.me':
            raise IOError
        elif url == 'http://www.djangoproject.com/offsite_redirect':
            resp = MockHttpResponse(url = 'http://www.other-site.com')
            content = open(TEST_HTML).read()
        else:
            resp = MockHttpResponse(url)
            content = open(TEST_HTML).read()
        return resp, content

def mock():
    httplib2.Http = MockHttp

def unmock():
    httplib2.Http = MockHttp.h

def test_parse_html():
    p = Patu(urls=[TEST_URL])
    r = p.get_urls(MockHttp(), TEST_URL)
    eq_(r.links, LINKS)

def test_spinner():
    s = Spinner()
    for x in xrange(0,6):
        s.spin()
    eq_(s.status, 2)

@with_setup(mock, unmock)
def test_crawl():
    p = Patu(urls=[TEST_URL], depth=1)
    p.crawl()
    eq_(p.seen_urls, SEEN_URLS)

@with_setup(mock, unmock)
def test_generate():

    with open('.test_generated.txt', 'w') as f:
        s = sys.stdout
        sys.stdout = f

        p = Patu(urls=[TEST_URL], depth=1, generate=True)
        p.crawl()

        sys.stdout = s
    with open('.test_generated.txt', 'r') as f:
        generated_urls = f.read().strip()
    remove('.test_generated.txt')
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
    eq_(generated_urls, correct_urls)

@with_setup(mock, unmock)
def test_stdin():
    with open(TEST_INPUT) as f:
        s = sys.stdin
        sys.stdin = f

        p = Patu(depth=1, input_file='-', verbose=True)
        p.crawl()

        sys.stdin = s
    eq_(p.seen_urls, SEEN_URLS)

@with_setup(mock, unmock)
def test_file_input():
    p = Patu(depth=1, input_file=TEST_INPUT)
    p.crawl()
    eq_(p.seen_urls, SEEN_URLS)

@with_setup(mock, unmock)
def test_no_http():
    p = Patu(urls=['www.djangoproject.com'], depth=1)
    p.crawl()
    eq_(p.seen_urls, SEEN_URLS)

@with_setup(mock, unmock)
def test_worker():
    p = Patu(urls=['www.djangoproject.com'], depth=1)
    for url, referer in p.next_urls.iteritems():
        p.task_queue.put(url)
    p.task_queue.put('STOP')
    p.worker()
    content = p.done_queue.get().content

    with open(TEST_HTML) as f:
        eq_(f.read(), content)

@with_setup(mock, unmock)
def test_worker_statuses():
    """
    This is kind of wanking - just trying to get test coverage in the worker
    processes
    """
    url_statuses = [
        ('www.djangoproject.com/offsite_redirect', 200),
        ('error.me', 500),
        ('io.me', -1),
        ('keyboard.me', -1)
        ]

    for address, error_code in url_statuses:
        p = Patu(urls=[address], depth=1)
        for url, referer in p.next_urls.iteritems():
            p.task_queue.put(url)
        p.task_queue.put('STOP')
        p.worker()
        u = p.done_queue.get()
        eq_(u.status_code, error_code)

@with_setup(mock, unmock)
def test_worker_input_file():
    p = Patu(urls=['www.djangoproject.com'], depth=1, input_file=TEST_INPUT)
    for url, referer in p.next_urls.iteritems():
        p.task_queue.put(url)
    p.task_queue.put('STOP')
    p.worker()
    p.done_queue.put('STOP')
    for u in iter(p.done_queue.get, 'STOP'):
        try:
            url = u.url
        except AttributeError:
            url = False
        assert url in SEEN_URLS or not url

@with_setup(mock, unmock)
def test_error():
    with open('.test_generated.txt', 'w') as f:
        s = sys.stdout
        sys.stdout = f

        p = Patu(urls=['error.me'], depth=1)
        p.crawl()

        sys.stdout = s
    with open('.test_generated.txt', 'r') as f:
        eq_(f.read().strip(), '[500] http://error.me (from None)')

@with_setup(mock, unmock)
def test_main_process_keyboard():
    p = Patu(urls=['www.djangoproject.com'], depth=1)
    def ctrl_c():
        raise KeyboardInterrupt
    p.process_next_url = ctrl_c
    p.crawl()
    eq_(p.seen_urls, set([]))

@with_setup(mock, unmock)
def test_redirect():
    p = Patu(urls=['www.djangoproject.com'])
    r = p.get_urls(MockHttp(), 'http://www.djangoproject.com/offsite_redirect')
    eq_(r.url, 'http://www.djangoproject.com/offsite_redirect')
    eq_(r.links, [])
    eq_(r.status_code, 200)

@with_setup(mock, unmock)
def test_initial_redirect():
    p = Patu(urls=['redirect.me'], depth=2)
    p.crawl()
    eq_(p.seen_urls, SEEN_URLS)
    p = Patu(urls=['djangoproject.com'], depth=2)
    p.crawl()
    eq_(p.seen_urls, SEEN_URLS)

@with_setup(mock, unmock)
def test_options():
    with open('.test_generated.txt', 'w') as f:
        s = sys.stdout
        sys.stdout = f

        sys.argv = ['patu.py', 'error.me']

        main()

        sys.stdout = s
    with open('.test_generated.txt', 'r') as f:
        eq_(f.read().strip(), '[500] http://error.me (from None)')
