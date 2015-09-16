import util
import pandas as pd
import urllib
import os


years = range(2003, 2015)
boroughs = ['manhattan', 'bronx', 'brooklyn', 'queens', 'statenisland']
boroughNames = dict(zip(boroughs, boroughs))
urlBase = 'http://www1.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales'


for borough in boroughs:
    for year in years:
        newURL = os.path.join(urlBase, str(year),
                              '%s_%s.xls' % (year, boroughNames[borough]))
        newFile = urllib.URLopener()
        try:
            print('First try year: %s' % year)
            newFile.retrieve(newURL, 'data/%s_%s.xls' % (borough, year))
        except IOError:
            print('Excepted our year: %s' % year)
            if year < 2007:
                tmpurlBase = 'http://www1.nyc.gov/assets/finance/downloads'
                boroughNames['statenisland'] = 'si'
                newURL = os.path.join(tmpurlBase,
                                      'sales_%s_%s.xls' %
                                      (boroughNames[borough], str(year)[2:]))
                newFile.retrieve(newURL, 'data/%s_%s.xls' % (borough, year))
                boroughNames['statenisland'] = 'statenisland'  # reset
                continue
            elif year == 2007:
                tmpurlBase = 'http://www1.nyc.gov/assets/finance/downloads/excel/rolling_sales'
                newURL = os.path.join(tmpurlBase,
                                      'sales_%s_%s.xls' %
                                      (str(year), boroughNames[borough]))
                newFile.retrieve(newURL, 'data/%s_%s.xls' % (borough, year))
            elif year == 2008:
                tmpurlBase = 'http://www1.nyc.gov/assets/finance/downloads/pdf/09pdf/rolling_sales'
                newURL = os.path.join(tmpurlBase,
                                      'sales_%s_%s.xls' %
                                      (str(year), boroughNames[borough]))
                newFile.retrieve(newURL, 'data/%s_%s.xls' % (borough, year))
            elif year == 2009:
                newURL = os.path.join(urlBase,
                                      '%s_%s.xls' % (year, boroughNames[borough]))
                newFile = urllib.URLopener()
                newFile.retrieve(newURL, 'data/%s_%s.xls' % (borough, year))

def readData(borough, year):
    fn = 'data/%s_%s.xls' % (borough, year)
    if year < 2011:
        return pd.read_excel(fn, header=3)
    else:
        return pd.read_excel(fn, header=4)

for borough in boroughs:
    for year in years:
        tmpdata = readData(borough, year)
        tmpdata.columns = [column.rstrip('\n') for column in tmpdata.columns]
        try:
            fulldata = pd.concat([fulldata, tmpdata], axis=0)
        except NameError:
            fulldata = tmpdata
