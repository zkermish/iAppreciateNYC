'''notes on scraping streeteasy

#below gets to december 1999
http://streeteasy.com/closings/nyc/type:coop,condo%7Csqft%3E=600?page=12300&sort_by=date_desc


'''
from lxml import html
import requests
import mechanize
import cookielib
import BeautifulSoup
import numpy as np
import os
import urlparse
import urllib
import pandas as pd

from getGeocodes import *
from credentials import streeteasy_login, streeteasy_passwd

neighborhoodMapping = util.pickle_load('data/neighborhoodMapping.pkl')

# Browser
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
br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

br.addheaders = [('User-agent', 'Chrome')]

# The site we will navigate into, handling it's session
br.open('https://streeteasy.com/nyc/user/sign_in?return_to=')

# View available forms
for f in br.forms():
    print f

# Select the second (index one) form (the first form is a search query box)
br.select_form(nr=3)

# User credentials
br.form['login'] = streeteasy_login
br.form['password'] = streeteasy_passwd
# Login
br.submit()

def timeoutSafeOpen(br, url):
    try :
        br.open(url)
    except:
        #error httperror_seek_wrapper??
        print('Timed out. Waiting...')
        time.sleep(2)
        timeoutSafeOpen(br, url)

def sePageToDF(url):

    timeoutSafeOpen(br, url)

    soup = BeautifulSoup.BeautifulSoup(br.response().read())
    addresses = [address.text
                 for address in soup.findAll('div', {'class': 'details-title'})]
    sellPrices = [float(price.text.replace(',', '').lstrip('$'))
                  for price in soup.findAll('span',  {'class': 'price'})]
    sellDates = pd.to_datetime([date.text.lstrip('&nbsp;Sold ')
                               for date in soup.findAll('span', {'class': 'secondary_text accent_text'})])

    neighborhood = {}
    numSqft = {}
    numBdrms = {}
    numBthrms = {}
    for i, listing in enumerate(soup('div', {'class': 'details row'})):
        numBdrms[i] = None
        numBthrms[i] = None
        numSqft[i] = None
        for element in listing('div', {'class': 'details_info'}):
            if element.a:
                neighborhood[i] = element.a.text
            elif element.span:
                try:
                    print('First sqft attempt')
                    numSqft[i] = float(element.findNext('span', {'class': 'last_detail_cell'}).text.rstrip('ft&sup2;').replace(',', ''))
                    #numSqft.append(float(element.findNext('span', {'class': 'last_detail_cell'}).text.rstrip('ft&sup2;').replace(',', '')))
                    #try Sqft first to except on errors if no sqft given
                    try:
                        numBdrms[i] = float(element.findNext('span', {'class': 'first_detail_cell'}).text.rstrip('+ beds'))
                    except ValueError:
                        numBdrms[i] = 0.0 #studio
                    try:
                        numBthrms[i] = float(element.findNext('span', {'class': 'detail_cell'}).text.rstrip('+ baths').replace(',', ''))
                    except AttributeError:
                        # not well structure bedrooms & bathrooms, skip listing
                        numBthrms[i] = None
                        numBdrms[i] = None
                except ValueError:
                    print('except on sqft attempt')
                    # no square footage
                    numBthrms[i] = float(element.findNext('span', {'class': 'last_detail_cell'}).text.rstrip('+ baths'))
                    try:
                        numBdrms[i] = float(element.findNext('span', {'class': 'first_detail_cell'}).text.rstrip('+ beds'))
                    except ValueError:
                        numBdrms[i] = 0.0 #studio
            else:
                try:
                    numSqft[i] = float(element.text.rstrip('ft&sup2;').replace(',', ''))
                except ValueError:
                    #no square footage, no span
                    try:
                        numBdrms[i] = float(element.text.rstrip('+ beds'))
                    except ValueError:
                        numBdrms[i] = 0.0  # studio

    df = pd.DataFrame({'address': pd.Series(addresses),
                       'sellPrice': pd.Series(sellPrices),
                       'sellData': pd.Series(sellDates),
                       'bedrooms': pd.Series(numBdrms.values()),
                       'bathrooms': pd.Series(numBthrms.values()),
                       'sqft': pd.Series(numSqft.values()),
                       'neighborhood': pd.Series(neighborhood.values())})

    getaddressQuery(df)
    df['geoObj'] = df['addressToQuery'].apply(getGeoObj)

    return df

def getaddressQuery(df):
    '''pass data frame with 'address' and 'neighborhood' columns
    returns query with Borough mapped.
    '''
    try:
        df['addressToQuery'] = df['address'].apply(lambda x: x.split('#')[0]) \
            + ', ' \
            + df['neighborhood'].apply(lambda x: neighborhoodMapping[x]) \
            + ', NY'
    except KeyError as missingNeighborhood:
        print('Need new neighborhood for %s!' % missingNeighborhood.message)
        baseUrl = 'http://streeteasy.com/area'
        neighborhood = str(missingNeighborhood.message).lower().replace(' ', '-').replace('/', '-').translate(None, '()')
        nbhdurl = os.path.join(baseUrl, neighborhood)
        print(nbhdurl)
        try:
            borough = scrapeAreaPage(nbhdurl)
        except AttributeError:
            print('I am a borough')
            borough = neighborhood
            neighborhoodMapping[missingNeighborhood.message] = borough
            util.pickle_save(neighborhoodMapping, 'data/neighborhoodMapping.pkl')

        df['addressToQuery'] = df['address'].apply(lambda x: x.split('#')[0]) \
            + ', ' \
            + df['neighborhood'].apply(lambda x: neighborhoodMapping[x]) \
            + ', NY'
    return

def scrapeAreaPage(url):
    br.open(url)

    soup = BeautifulSoup.BeautifulSoup(br.response().read())
    borough = soup.find('div', {'class': 'box_info'}).p.text.split(',')[1]
    return borough


def getNeighborhoodMapping(neighborhoods):
    '''Scrape streeteasy's neighborhood description pages to get a
    neighborhood->borough mapping.
    returns a dict with neighborhood as key, borough as value
    '''
    # got neighborhoods from neighborhoods = fulldata['neighborhood'].unique()
    # baseUrl = 'http://streeteasy.com/area/springfield-gardens'
    baseUrl = 'http://streeteasy.com/area'
    neighborhoodMapping = {}
    urls = map(lambda x:
               os.path.join(baseUrl,
                            str(x).lower().replace(' ', '-').replace('/', '-').translate(None, '()')), neighborhoods)
    for neighborhood, url in zip(neighborhoods, urls):
        print('%s URL: %s' % (neighborhood, url))
        try:
            neighborhoodMapping[neighborhood] = scrapeAreaPage(url)
        except AttributeError:
            print('I am a borough')
            neighborhoodMapping[neighborhood] = neighborhood
    return neighborhoodMapping

def main(fulldata = None, pages= np.arange(1,6000)):

    url = 'http://streeteasy.com/closings/nyc/type:coop,condo%7Csqft%3E=600?page=12300&sort_by=date_desc'
    parts = urlparse.urlparse(url)
    query = dict(urlparse.parse_qsl(parts.query))
    for page in pages:
        query.update({'page': page})
        encoded = urllib.urlencode(query, doseq=True)
        newurl = urlparse.ParseResult(parts.scheme, parts.netloc, parts.path, parts.params, encoded, parts.fragment).geturl()
        print newurl
        tmpdf = sePageToDF(newurl)
        print('Saving...')
        util.pickle_save(tmpdf, 'data/SE_pg_%s.pkl' % page)
        try:
            print('Concating...')
            fulldata = pd.concat([fulldata, tmpdf], axis=0, ignore_index=True)
        except NameError:
            fulldata = tmpdf
        print('Total rows: %s' % len(fulldata))

if __name__=='__main__':
    main()
