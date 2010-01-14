#!/usr/bin/env python

# TODO
# breadth-first searching, stopping after a given level
# ensure redirects are followed

import httplib2
import sys
from pyquery import PyQuery
from optparse import OptionParser
from multiprocessing import Process, Queue, current_process
from urlparse import urlsplit, urljoin, urlunsplit


class Spinner(object):
    def __init__(self):
        self.status = 0
        self.locations = ['|', '/', '-', '\\']

    def spin(self):
        sys.stderr.write("%s\r" % self.locations[self.status])
        sys.stderr.flush()
        self.status = (self.status + 1) % 4

class Patu(object):
    processes = []
    # Create queues
    task_queue = Queue()
    done_queue = Queue()
    next_urls = {}

    def __init__(self, url, spiders=1, spinner=True, verbose=False, depth=-1, breadth=False):
        self.url = url
        if not url.startswith('http://'):
            self.url = "http://" + self.url
        self.constraint = urlsplit(self.url).netloc
        self.next_urls[self.url] = True
        self.spiders = spiders
        self.spinner = spinner
        self.verbose = verbose
        self.depth = depth
        self.breadth = breadth

    def worker(self):
        """
        Function run by worker processes
        """
        try:
            h = httplib2.Http(timeout = 60)
            for url in iter(self.task_queue.get, 'STOP'):
                result = self.get_url(h, url)
                self.done_queue.put(result)
        except KeyboardInterrupt:
            pass

    def get_url(self, h, url):
        """
        Function used to calculate result
        """
        links = []
        try:
            resp, content = h.request(url)
            html = PyQuery(content)
        except Exception, e:
            return (current_process().name, '', url, links)
        hrefs = [a.attrib['href'] for a in html("a") if a.attrib.has_key('href')]
        for href in hrefs:
            absolute_url = urljoin(resp['content-location'], href.strip())
            parts = urlsplit(absolute_url)
            if parts.netloc in [self.constraint, ""] and parts.scheme in ["http", ""]:
                # Ignore the #foo at the end of the url
                no_fragment = parts[:4] + ("",)
                links.append(urlunsplit(no_fragment))
        return (current_process().name, resp.status, url, links)

    def crawl(self):
        seen_urls = {}
        # The ones we're currently scanning
        queued_urls = {}
        # For the next level
        current_depth = 0
        spinner = Spinner()

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
                for k, v in self.next_urls.iteritems():
                    queued_urls[k] = v
                    self.task_queue.put(k)
                self.next_urls = {}

                while len(queued_urls) > 0:
                    name, resp_status, url, links = self.done_queue.get()
                    if resp_status == 200:
                        if self.verbose:
                            print "[%s] %s (from %s)" % (resp_status, url, queued_urls[url])
                            sys.stdout.flush()
                        elif self.spinner:
                            spinner.spin()
                    else:
                        print "[%s] %s (from %s)" % (resp_status, url, queued_urls[url])
                        sys.stdout.flush()
                    del(queued_urls[url])
                    seen_urls[url] = True
                    for link in links:
                        if link not in seen_urls and link not in queued_urls:
                            # remember what url referenced this link
                            self.next_urls[link] = url
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
        print

if __name__ == '__main__':
    parser = OptionParser()
    options_a = [
        ["-s", "--spiders", dict(dest="spiders", type="int", default=1, help="sends more than one spider")],
        ["-S", "--nospinner", dict(dest="spinner", action="store_false", default=True, help="turns off the spinner")],
        ["-v", "--verbose", dict(dest="verbose", action="store_true", default=False, help="outputs every request (implies --nospiner)")],
        ["-d", "--depth", dict(dest="depth", type="int", default=-1, help="does a breadth-first crawl, stopping after DEPTH levels (implies --breadth)")],
        ["-b", "--breadth", dict(dest="breadth", action="store_true", default=False, help="does a breadth-first crawl; may be used with --depth")],
    ]
    for s, l, k in options_a:
        parser.add_option(s, l, **k)
    (options, args) = parser.parse_args()
     # Submit first url
    try:
        url = unicode(args[0])
    except IndexError:
        print "Give the spiders a URL."
        sys.exit(1)
    kwargs = {
        'url': url,
        'spiders': options.spiders,
        'spinner': options.spinner,
        'verbose': options.verbose,
        'depth': options.depth,
        'breadth': options.breadth,
    }
    spider = Patu(**kwargs)
    spider.crawl()

