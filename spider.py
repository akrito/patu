#!/usr/bin/env python

import httplib2
import time
import random
import sys
from BeautifulSoup import BeautifulSoup
from optparse import OptionParser
from multiprocessing import Process, Queue, current_process
from urlparse import urlsplit, urljoin


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
    try:
        links = []
        resp, content = h.request(url)
        soup = BeautifulSoup(content)
        hrefs = [a['href'] for a in soup.findAll('a') if a.has_key('href')]
        for href in hrefs:
            parts = urlsplit(href.strip())
            if parts.netloc in [constraint, ""] and parts.scheme in ["http", ""]:
                harvested_link = urljoin(url, href)
                links.append(harvested_link)
    except:
        links = []
        resp = None
    return (current_process().name, resp, url, links)

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
            name, resp, url, links = done_queue.get()
            if resp and resp.status == 200:
                spinner.spin()
            elif resp:
                print "[%s] %s (from %s)" % (resp.status, url, queued_urls[url])
                sys.stdout.flush()
            else:
                print "[ERROR] %s (from %s)" % (url, queued_urls[url])
                sys.stdout.flush()
            del(queued_urls[url])
            seen_urls[url] = True
            for link in links:
                if not seen_urls.has_key(link) and not queued_urls.has_key(link):
                    # remember what url referenced this link
                    queued_urls[link] = url
                    task_queue.put(link)
        
        for i in range(options.spiders):
            task_queue.put('STOP')
    except KeyboardInterrupt:
        pass
    finally:
        for p in processes:
            p.join()
    print

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-s", "--spiders", dest="spiders", type="int", default=1, help="how many spiders to send")
    parser.add_option("-S", "--nospinner", dest="spinner", action="store_false", default=True)
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False)
    parser.add_option("-d", "
    parser.add_option("
    parser.add_option("
    # TODO follow redirects?
    (options, args) = parser.parse_args()
    test(options, args)
