import numpy as np


def geocalc(lat0, lon0, lat1, lon1):
    """Return the distance (in km) between two points in
    geographical coordinates."""
    EARTH_R = 6372.8

    lat0 = np.radians(lat0)
    lon0 = np.radians(lon0)
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    dlon = lon0 - lon1
    y = np.sqrt(
            (np.cos(lat1) * np.sin(dlon)) ** 2
         + (np.cos(lat0) * np.sin(lat1)
         - np.sin(lat0) * np.cos(lat1) * np.cos(dlon)) ** 2)
    x = np.sin(lat0) * np.sin(lat1) + \
        np.cos(lat0) * np.cos(lat1) * np.cos(dlon)
    c = np.arctan2(y, x)
    return EARTH_R * c


def getStationDistances(df, subwayStations):
    '''Input data frame df and subwayStations info dictionary.
    Returns same data frame with new columns
    '''
    for station in subwayStations['stations']:
        print('On station %s' % station['name'])
        df[station['name'] + '_distance'] = \
            df['geoObj'].apply(lambda x: geocalc(x.latitude, x.longitude,
                                                 float(station['latitude']),
                                                 float(station['longitude'])))
