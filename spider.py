#!/usr/bin/env python

# TODO
# breadth-first searching, stopping after a given level
# ensure redirects are followed

import httplib2
import time
import random
import sys
from BeautifulSoup import BeautifulSoup
from optparse import OptionParser
from multiprocessing import Process, Queue, current_process
from urlparse import urlsplit, urljoin, urlunsplit


class Spinner:
    def __init__(self):
        self.status = 0
        self.locations = ['|', '/', '-', '\\']
        
    def spin(self):
        sys.stderr.write("%s\r" % self.locations[self.status])
        sys.stderr.flush()
        self.status = (self.status + 1) % 4

def worker(input, output, constraint):
    """
    Function run by worker processes
    """
    try:
        h = httplib2.Http(timeout = 60)
        for url in iter(input.get, 'STOP'):
            result = get_url(h, url, constraint)
            output.put(result)
    except KeyboardInterrupt:
        pass

def get_url(h, url, constraint):
    """
    Function used to calculate result
    """
    links = []
    try:
        resp, content = h.request(url)
    except Exception, e:
        return (current_process().name, e[0], url, links)
    soup = BeautifulSoup(content)
    hrefs = [a['href'] for a in soup.findAll('a') if a.has_key('href')]
    for href in hrefs:
        absolute_url = urljoin(url, href.strip())
        parts = urlsplit(absolute_url)
        if parts.netloc in [constraint, ""] and parts.scheme in ["http", ""]:
            # Ignore the #foo at the end of the url
            no_fragment = parts[:4] + ("",)
            links.append(urlunsplit(no_fragment))
    return (current_process().name, resp.status, url, links)

def test(options, args):
   
    seen_urls = {}
    queued_urls = {}
    processes = []
    spinner = Spinner()
    
    # Create queues
    task_queue = Queue()
    done_queue = Queue()

    # Submit first url
    try:
        url = unicode(args[0])
    except IndexError:
        print "Give the spiders a URL."
        sys.exit(1)
    if not url.startswith('http://'):
        url = "http://" + url
    host = urlsplit(url).netloc
    task_queue.put(url)
    queued_urls[url] = True
    
    try:
    
        # Start worker processes
        for i in range(options.spiders):
            p = Process(target=worker, args=(task_queue, done_queue, host))
            p.start()
            processes.append(p)
            
        while len(queued_urls) > 0:
            name, resp_status, url, links = done_queue.get()
            if resp_status == 200:
                if options.verbose:
                    print "[%s] %s (from %s)" % (resp_status, url, queued_urls[url])
                    sys.stdout.flush()
                elif options.spinner:
                    spinner.spin()
            else:
                print "[%s] %s (from %s)" % (resp_status, url, queued_urls[url])
                sys.stdout.flush()
            del(queued_urls[url])
            seen_urls[url] = True
            for link in links:
                if not seen_urls.has_key(link) and not queued_urls.has_key(link):
                    # remember what url referenced this link
                    queued_urls[link] = url
                    task_queue.put(link)
    except KeyboardInterrupt:
        pass
    finally:
        for i in range(options.spiders):
            task_queue.put('STOP')
        for p in processes:
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
    test(options, args)
