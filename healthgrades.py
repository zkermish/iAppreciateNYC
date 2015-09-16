import util
import pandas as pd

healthgrades = \
    pd.read_csv('data/DOHMH_New_York_City_Restaurant_Inspection_Results.csv')
healthgrades = healthgrades[healthgrades['INSPECTION DATE'] != '01/01/1900']

healthgrades['INSPECTION DATE'] = \
    pd.to_datetime(healthgrades['INSPECTION DATE'])

healthgrades['GRADE DATE'] = \
    pd.to_datetime(healthgrades['GRADE DATE'])

firstinspection = \
    healthgrades.sort(['CAMIS', 'INSPECTION DATE']).groupby('CAMIS').first()

tocount = firstinspection.sort(['ZIPCODE', 'INSPECTION DATE'])[['ZIPCODE', 'INSPECTION DATE']]
monthlyCount = tocount.groupby(pd.Grouper(key='INSPECTION DATE', freq='M'))['ZIPCODE'].value_counts().unstack()


# Billburg
# neighborhood = 'Bushwick and Williamsburg'
for neighborhood in neighborhooddict.keys():
    figure()
    for zipcode in neighborhooddict[neighborhood]:
        if zipcode in fulldata.columns:
            ax1 = subplot(211)
            title(neighborhood)
            plot_date(fulldata[zipcode].index, fulldata[zipcode],
                      alpha=0.7, fmt='.')
            ylabel('Price per square foot ($)')
            setp(ax1.get_xticklabels(), visible=False)

            subplot(212, sharex=ax1)
            plot_date(monthlyCount.index, monthlyCount[zipcode],
                      alpha=0.7, fmt='--')
            xlabel('Date')
            ylabel('Monthly first inspection count')
    savefig('plots/%s.png' % neighborhood)
    close()
