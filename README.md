Patu
====

A small spider, useful for checking a site for 404s and 500s. Patu requires httplib2 and lxml:

    pip install -U httplib2 lxml

Quick Usage
===========

To see available options:

    patu.py --help

To spider an entire site using 5 workers, only showing errors:

    patu.py --spiders=5 www.example.com
    
To spider, stopping after the first level of links:

    patu.py --depth=1 www.example.com
    
To get a list of every linked page on a site:

    patu.py --generate www.example.com > urls.txt
    
Instead of spidering for URLs, use a file instead and show all responses:

    patu.py --input=urls.txt --verbose www.example.com

Format of URLs File
===================

The output produced by <code>--generate</code> is formatted like so:

    FIRST_URL<TAB>None
    LINK1<TAB>REFERER
    LINK2<TAB>REFERER
    
<code>--input</code> can take a file of that format, or one URL per line with no referer. <code>--input=-</code> reads from stdin.

Testing
=======

Patu uses Nose for testing. To install Nose and test:

    pip install -U nose
    nosetests

