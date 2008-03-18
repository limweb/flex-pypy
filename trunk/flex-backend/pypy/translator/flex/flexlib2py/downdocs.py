#!/usr/bin/env python

import urllib2
import os.path
import sys
import re
import string

url_root = "http://livedocs.adobe.com/flex/3/langref/package-summary.html"
url_root = "file:///Users/gui/Downloads/flex3_documentation/langref/package-summary.html"

dump_file = open('dump.txt', 'w')

def get_page(url):
    # print ">> GET: " + url
    page = urllib2.urlopen(url)
    page = page.read()
    assert page, "Page is empty"
    return page
    
re_all = re.compile(r'href="([\w/]*\w+/package-detail\.html)"\>([\w.]*\w+)\</a\>')
def get_all(url):
    page = get_page(url)
    r = re_all
    m = r.findall(page)
    u = os.path.dirname(url)
    for url, name in m:
        url = os.path.join(u, url)
        dump_file.write("p: %s\n" % name)
        get_package(url)

re_package = re.compile(r'summaryTableSecondCol">\<a href="(\w+\.html)">(\w+)')
def get_package(url):
    page = get_page(url)
    r = re_package
    m = r.findall(page)
    u = os.path.dirname(url)
    for url, name in m:
        url = os.path.join(u, url)
        dump_file.write("c: %s\n" % name)
        get_class(url)

re_class_inheritance_a = re.compile(r'inheritanceList">(.*)<\/td>')
re_class_inheritance_b = re.compile(r'<img[^>]*>')
re_class_inheritance_c = re.compile(r'<a\s*href="([^"]+)"\s*>([\w\s]+)</a>')
def get_class_inheritance(page):
    r = re_class_inheritance_a
    m = r.search(page)
    if m:
        s = m.groups()[0]
        s = re_class_inheritance_b.sub('', s)
        m = re_class_inheritance_c.findall(s)
        for url, name in m:
            url = url.lstrip("./")
            if url.endswith('.html'):
                url = url[:-5]
            url = url.replace('/', '.')
            dump_file.write('i: %s\n' % url)
    else:
        m = re.search(r'<title>(.*)</title>', page)
        if m:
            print "Could not find inheritance chain in: '%s'" % m.groups()[0]
        else:
            raise Exception("Don't understand format of file:\n" + page)


def get_class(url):
    page = get_page(url)
    get_class_inheritance(page)
    r = re.compile(r"""<div class="detailBody">\s*<code>(.*)</code>""")
    u = re.compile(r'href="(http://)?(?P<url>[\w/._*]+)\.html(#([\w_*]+))?"')
    a = re.compile(r'([\w_*]+)\s*<\/a>\s*$')
    t = re.compile(r'<[^>]+>')
    m = r.findall(page)
    for raw in m:
        raw = raw.strip()
        s = t.sub('', raw)
        if s.find('function') >= 0:
            v = u.findall(raw)
            if not a.search(raw):
                typ = ':void'
                s = s.rstrip(string.letters + string.whitespace + ':')
            elif v:
                s = s.rstrip(string.letters + string.whitespace)
                typ = v[-1][1]
                typ = typ.lstrip().lstrip('/.:')
                if typ in ['specialTypes']:
                    typ = v[-1][3]
                typ = typ.replace('/', '.')
            else:
                typ = ''
            dump_file.write("f: %s%s\n" % (s, typ))
        elif s.find(' const ') >= 0:
            dump_file.write("k: %s\n" % s)
        else:
            dump_file.write("a: %s\n" % s)



get_all(url_root)
# get_class('http://livedocs.adobe.com/flex/3/langref/air/net/ServiceMonitor.html')
