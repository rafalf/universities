import logging
import time
import os
import sys
import mechanize
import cookielib
import csv

#
#    WE MIGHT USE THAT FOR OTHER SITES
#
#
logger = logging.getLogger('u.usc')


def register():

    rcsv = _read_univs()
    for univ in rcsv:
        if '{}_register.py'.format(univ[0]) == os.path.basename(__file__):
            reg_url = univ[1]
            break

    try:

        br = mechanize.Browser()

        # Cookie Jar
        cj = cookielib.LWPCookieJar()
        br.set_cookiejar(cj)

        # Browser options
        br.set_handle_equiv(True)
        br.set_handle_gzip(True)
        br.set_handle_redirect(True)
        br.set_handle_referer(True)
        br.set_handle_robots(False)

        # Follows refresh 0 but not hangs on refresh > 0
        br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

        # act as chrome
        br.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko')]

        r = br.open(reg_url)
        html = r.read()
        print html

        # Show the available forms
        for f in br.forms():
            print f

        br.select_form(nr=0)
        br.form['BusinessCode'] = 'a'
        br.submit()

        # print br.response().read()

        # Iterate the links
        for link in br.links():
            print link.text, link.url

        # Looking for the Customers link (if the link is not found you would have to
        # handle a LinkNotFoundError exception)
        cust_link = br.find_link(url='#/customers')
        print(cust_link.url)

        br.click_link(cust_link)
        br.follow_link(cust_link)

        # print br.response().read()
        print br.geturl()

    except mechanize._mechanize.LinkNotFoundError:
        logger.debug('Log in failed')
        pass

    # Iterate the links
    time.sleep(10)
    for link in br.links():
        print link.text, link.url


def set():

    log_file = os.path.join(os.path.dirname(__file__), 'logs',
                                time.strftime('%d%m%y%H%M', time.localtime()) + "_scraper.log")
    file_hndlr = logging.FileHandler(log_file)
    logger.addHandler(file_hndlr)
    console = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(console)
    ch = logging.Formatter('[%(levelname)s] %(message)s')
    console.setFormatter(ch)
    file_hndlr.setFormatter(ch)
    logger.setLevel(logging.getLevelName('DEBUG'))


def _read_univs():
    with open('urls.csv', 'rb') as hlr:
        rd = csv.reader(hlr, delimiter=',', quotechar='"')
        return [row for row in rd if row[1] != "#Name"]


if __name__ == '__main__':
    set()
    register()