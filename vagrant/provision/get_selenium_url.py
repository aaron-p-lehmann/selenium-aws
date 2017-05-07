"""
Get the url to the latest version of the Selenium standalone server.
"""

import urllib2
import xml.etree.ElementTree 

selenium_download_server = "https://selenium-release.storage.googleapis.com/"
selenium_docroot = "http://doc.s3.amazonaws.com/2006-03-01"

# Make an ElementTree out of the index page for the selenium versions
index_tree = xml.etree.ElementTree.fromstring(urllib2.urlopen("%s?delimiter=/&prefix=" % selenium_download_server).read())

# Get the most recent version of Selenium
version = [prefix.text for prefix in index_tree.findall(".//{%s}Prefix" % selenium_docroot) if prefix.text and prefix.text[0] in "0123456789."][-1]

# Make an ElementTree out of the software involved in the latest version of selenium
version_tree = xml.etree.ElementTree.fromstring(urllib2.urlopen("%s?delimiter=/&prefix=%s" % (selenium_download_server, version)).read())

# Get the absolute path from the server for the jarfile for the selenium standalone server
jarfile = [key.text for key in version_tree.findall(".//{%s}Key" % selenium_docroot) if key.text and "selenium-server-standalone" in key.text][0]

# Stitch it together and print it out
print "%s%s" % (selenium_download_server, jarfile)
