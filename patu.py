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
    def __init__(self, url, status_code=-1, content=None, links=[]):
        self.url = url
        self.status_code = status_code
        self.content = content
        self.links = links

class Patu(object):

    def __init__(self, urls=[], spiders=1, spinner=True, verbose=False, depth=-1, input_file=None, generate=False):
        # Set up the multiprocessing bits
        self.processes = []
        self.task_queue = Queue()
        self.done_queue = Queue()
        self.next_urls = {}
        self.queued_urls = {}
        self.seen_urls = set()
        self.spinner = Spinner()

        # Generate the initial URLs, either from command-line, stdin, or file
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
            h = httplib2.Http(timeout = 60)
            for url in urls:
                if not url.startswith("http://"):
                    url = "http://" + url
                # Follow initial redirects here to set self.constraints
                try:
                    resp, content = h.request(url)
                    url = resp['content-location']
                except:
                    # This URL is no good. Keep it in the queue to show the
                    # error later
                    pass
                self.urls.append(url)
                self.next_urls[url] = None
            self.constraints = [''] + [urlsplit(url).netloc for url in self.urls]
        self.spiders = spiders
        self.show_spinner = spinner
        self.verbose = verbose
        self.depth = depth
        self.input_file = input_file
        self.generate = generate

    def worker(self):
        """
        Function run by worker processes
        """
        try:
            h = httplib2.Http(timeout = 60)
            for url in iter(self.task_queue.get, 'STOP'):
                result = self.get_urls(h, url)
                self.done_queue.put(result)
        except KeyboardInterrupt:
            self.done_queue.put(Response(url, -1))

    def get_urls(self, h, url):
        """
        Function used to calculate result
        """
        links = []
        try:
            resp, content = h.request(url)
            if self.input_file:
                # Short-circuit if we got our list of links from a file
                return Response(url, resp.status)
            elif resp.status != 200:
                return Response(url, resp.status)
            elif urlsplit(resp['content-location']).netloc not in self.constraints:
                # httplib2 follows redirects automatically
                # Check to make sure we've not been redirected off-site
                return Response(url, resp.status)
            else:
                html = fromstring(content)
        except Exception, e:
            print "%s %s" % (type(e), str(e))
            return Response(url)

        # Add relevant links
        for link in html.cssselect('a'):
            if not link.attrib.has_key('href'):
                # Skip links w/o an href attrib
                continue
            href = link.attrib['href']
            absolute_url = urljoin(resp['content-location'], href.strip())
            parts = urlsplit(absolute_url)
            if parts.netloc in self.constraints and parts.scheme == 'http':
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

                # place next urls into the task queue, possibly
                # short-circuiting if we're generating them
                for url, referer in self.next_urls.iteritems():
                    self.queued_urls[url] = referer
                    if self.generate and current_depth == self.depth:
                        self.done_queue.put(Response(url, 200))
                    else:
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

def main():
    parser = OptionParser()
    options_a = [
        ["-s", "--spiders", dict(dest="spiders", type="int", default=1, help="sends more than one spider")],
        ["-S", "--nospinner", dict(dest="spinner", action="store_false", default=True, help="turns off the spinner")],
        ["-v", "--verbose", dict(dest="verbose", action="store_true", default=False, help="outputs every request (implies --nospiner)")],
        ["-d", "--depth", dict(dest="depth", type="int", default=-1, help="does a breadth-first crawl, stopping after DEPTH levels")],
        ['-g', '--generate', dict(dest='generate', action='store_true', default=False, help='generate a list of crawled URLs on stdout')],
        ['-i', '--input', dict(dest='input_file', type='str', default='', help='file of URLs to crawl')],
    ]
    for s, l, k in options_a:
        parser.add_option(s, l, **k)
    (options, args) = parser.parse_args()
     # Submit first url
    urls = [unicode(url) for url in args]
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

if __name__ == '__main__':
    sys.exit(main())
