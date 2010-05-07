#!/usr/bin/env python

import httplib2
import sys
from lxml.html import fromstring
from optparse import OptionParser
from multiprocessing import Process, Queue
from urlparse import urlsplit, urljoin, urlunsplit


class Spinner(object):
    def __init__(self):
        self.status = 0
        self.locations = ['|', '/', '-', '\\']

    def spin(self):
        sys.stderr.write("%s\r" % self.locations[self.status])
        sys.stderr.flush()
        self.status = (self.status + 1) % 4

class Response(object):
    def __init__(self, url="", status_code=-1, content=None, links=[]):
        self.url = url
        self.status_code = status_code
        self.content = content
        self.links = links

class RedirectError(Exception):
    def __init__(self, location):
        self.location = location

class Patu(object):
    processes = []
    # Create queues
    task_queue = Queue()
    done_queue = Queue()
    next_urls = {}
    queued_urls = {}
    seen_urls = set()
    spinner = Spinner()

    def __init__(self, urls, spiders=1, spinner=True, verbose=False, depth=-1, breadth=False, input_file=None, generate=False):
        if input_file:
            if input_file == '-':
                f = sys.stdin
            else:
                f = open(input_file)
            for line in f:
                bits = line.strip().split("\t")
                if bits == ['']:
                    continue
                elif len(bits) == 1:
                    self.next_urls[bits[0]] = None
                else:
                    self.next_urls[bits[0]] = bits[1]
            f.close()
        else:
            self.urls = []
            for url in urls:
                if not url.startswith("http://"):
                    url = "http://" + url
                self.urls.append(url)
                self.next_urls[url] = None
            self.constraints = [''] + [urlsplit(url).netloc for url in self.urls]
        self.spiders = spiders
        self.show_spinner = spinner
        self.verbose = verbose
        self.depth = depth
        self.breadth = breadth
        self.input_file = input_file
        self.generate = generate

    def worker(self):
        """
        Function run by worker processes
        """
        try:
            h = httplib2.Http(timeout = 60)
            while True:
                for url in iter(self.task_queue.get, 'STOP'):
                    try:
                        result = self.get_urls(h, url)
                    except RedirectError, e:
                        self.task_queue.put(e.location)
                    else:
                        self.done_queue.put(result)
        except KeyboardInterrupt:
            pass

    def get_urls(self, h, url):
        """
        Function used to calculate result
        """
        links = []
        try:
            resp, content = h.request(url)
            if 300 <= resp.status < 400:
                raise RedirectError(resp.location)
            elif self.input_file:
                # Short-circuit if we got our list of links from a file
                return Response(url, resp.status)
            elif resp.status != 200:
                return Response(url, resp.status)
            else:
                html = fromstring(content)
        except Exception:
            return Response(url)

        # Add relevant links
        for link in html.cssselect('a'):
            if not link.attrib.has_key('href'):
                # Skip links w/o an href attrib
                continue
            if link.attrib.get('rel', None) == 'nofollow':
                # Skip links w/ rel="nofollow" (offsite)
                continue
            href = link.attrib['href']
            absolute_url = urljoin(resp['content-location'], href.strip())
            parts = urlsplit(absolute_url)
            if parts.netloc in self.constraints and parts.scheme in ['http', '']:
                # Ignore the #foo at the end of the url
                no_fragment = parts[:4] + ('',)
                links.append(urlunsplit(no_fragment))
        return Response(url, resp.status, content, links)

    def process_next_url(self):
        response = self.done_queue.get()
        referer = self.queued_urls[response.url]
        result = '[%s] %s (from %s)' % (response.status_code, response.url, referer)
        if response.status_code == 200:
            if self.verbose:
                print result
                sys.stdout.flush()
            elif self.generate:
                print "%s\t%s" % (response.url, referer)
            elif self.show_spinner:
                self.spinner.spin()
        else:
            print result
            sys.stdout.flush()
        self.seen_urls.add(response.url)
        del(self.queued_urls[response.url])
        for link in response.links:
            if link not in self.seen_urls and link not in self.queued_urls:
                # remember what url referenced this link
                self.next_urls[link] = response.url

    def crawl(self):
        # For the next level
        current_depth = 0
        try:
            # Start worker processes
            for i in range(self.spiders):
                p = Process(target=self.worker)
                p.start()
                self.processes.append(p)

            while len(self.next_urls) > 0 and (current_depth <= self.depth or self.depth == -1):
                if self.verbose:
                    print "Starting link depth %s" % current_depth
                    sys.stdout.flush()

                # place next urls into the task queue
                for url, referer in self.next_urls.iteritems():
                    self.queued_urls[url] = referer
                    self.task_queue.put(url)
                self.next_urls = {}

                while len(self.queued_urls) > 0:
                    self.process_next_url()
                current_depth += 1

        except KeyboardInterrupt:
            pass
        finally:
            # Give the spiders a chance to exit cleanly
            for i in range(self.spiders):
                self.task_queue.put('STOP')
            for p in self.processes:
                # Forcefully close the spiders
                p.terminate()
                p.join()

if __name__ == '__main__':
    parser = OptionParser()
    options_a = [
        ["-s", "--spiders", dict(dest="spiders", type="int", default=1, help="sends more than one spider")],
        ["-S", "--nospinner", dict(dest="spinner", action="store_false", default=True, help="turns off the spinner")],
        ["-v", "--verbose", dict(dest="verbose", action="store_true", default=False, help="outputs every request (implies --nospiner)")],
        ["-d", "--depth", dict(dest="depth", type="int", default=-1, help="does a breadth-first crawl, stopping after DEPTH levels (implies --breadth)")],
        ['-g', '--generate', dict(dest='generate', action='store_true', default=False, help='generate a list of crawled URLs on stdout')],
        ['-i', '--input', dict(dest='input_file', type='str', default='', help='file of URLs to crawl')],
    ]
    for s, l, k in options_a:
        parser.add_option(s, l, **k)
    (options, args) = parser.parse_args()
     # Submit first url
    try:
        urls = [unicode(url) for url in args]
    except IndexError:
        print "Give the spiders a URL."
        sys.exit(1)
    kwargs = {
        'urls': urls,
        'spiders': options.spiders,
        'spinner': options.spinner,
        'verbose': options.verbose,
        'depth': options.depth,
        'generate': options.generate,
        'input_file': options.input_file
    }
    spider = Patu(**kwargs)
    spider.crawl()
    print

