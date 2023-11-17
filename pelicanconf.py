#!/usr/bin/env python
AUTHOR = 'Victor Stinner'
SITENAME = 'Victor Stinner blog 3'
SITEURL = ''

PATH = 'content'

TIMEZONE = 'Europe/Paris'

DEFAULT_LANG = 'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (("Victor Stinner's Notes", 'http://vstinner.readthedocs.org/'),
        )

# Social widget
SOCIAL = (('Follow @VictorStinner on Twitter', 'https://twitter.com/VictorStinner'),
          )

DEFAULT_PAGINATION = 10

# Uncomment following line if you want document-relative URLs when developing
RELATIVE_URLS = True

# Fork of:
# https://github.com/getpelican/pelican-themes/tree/master/aboutwilson
# Modify the CSS:
#   - remove <p> margin.
#   - set font size from 13px to 16px
THEME = "aboutwilson"
