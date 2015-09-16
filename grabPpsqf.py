from lxml import html
import requests
import Quandl
import util
import pandas as pd

page = requests.get('https://www.health.ny.gov/statistics/ \
    cancer/registry/appendix/neighborhoods.htm')
tree = html.fromstring(page.text)
neighborhoods = tree.xpath('//td[@headers="header2"]/text()’)
zipcodes = tree.xpath('//td[@headers="header3"]/text()')

neighborhooddict = dict(zip(map(str.lstrip, neighborhoods), zipcodes))
for neighborhood in neighborhooddict.keys():
    neighborhooddict[neighborhood] = \
        [int(zipcode) for zipcode
         in neighborhooddict[neighborhood].split(',')]


def getData(zipcode):
    try:
        tmpdata = Quandl.get('ZILL/Z%s_MVSF' % zipcode,
                             authtoken='mdhRQEZwwfbrdroBUHoz')
        tmpdata.columns = [zipcode]
        return tmpdata
    except Quandl.DatasetNotFound:
        print('Zipcode %s not found' % zipcode)
        return None


totalzipcodes = 0
missing = 0
for neighborhood in neighborhooddict.keys():
    for zipcode in neighborhooddict[neighborhood]:
        totalzipcodes += 1
        try:
            len(fulldata)
            tmpdata = getData(zipcode)
            if tmpdata is None:
                missing += 1
                continue
            else:
                fulldata = pd.concat([fulldata, tmpdata], axis=1)
                filename = 'data/%s_%s.pkl' % (neighborhood, zipcode)
                util.pickle_save(tmpdata, filename)
        except NameError:
            # hack to instantiate first DataFrame
            fulldata = getData(zipcode)
            filename = 'data/%s_%s.pkl' % (neighborhood, zipcode)
            util.pickle_save(fulldata, filename)

print('Missing %d zipcodes of %d total' % (missing, totalzipcodes))

for zipcode in fulldata.keys():
    plot_date(fulldata[zipcode].index,
              fulldata[zipcode], alpha=0.7, fmt='.')

plot_date(fulldata.index, fulldata.mean(axis=1))
