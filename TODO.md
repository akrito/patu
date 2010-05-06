Bugs
----
* Should check the content type before parsing

Features
--------
* Resume capability (dbm full of json)
* Exclude patterns
* Split up generating and consuming URLs, so we can:
  * Spider a site, spitting out URLs
  * Re-run the spider, using the list of generated URLs
* Templated reporting: provide a baked-in default template
