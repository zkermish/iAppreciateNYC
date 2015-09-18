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
        df[station['name']] = \
            df['geoObj'].apply(lambda x: geocalc(x.latitude, x.longitude,
                                                 float(station['latitude']),
                                                 float(station['longitude'])))

def googlePlacesNearestSubway(lat,lon, radius=600):
    from googleplaces import GooglePlaces, types, lang
    import credentials
    google_places = GooglePlaces(credentials.google_key)
    query_result = google_places.nearby_search(lat_lng =
        {'lat': lat, 'lng': lon},
        radius = radius, types=[types.TYPE_SUBWAY_STATION], rankby='distance')
    try:
        return query_result.places[0]
    except IndexError:
        print('No subway nearby?')
        return None

def googleMapsTransitTimes(stairInfo):
    departure_time = datetime.datetime(2015, 9, 14, 9, 0, 0)
    directions_result = gmaps.directions(origin, destination, mode='transit',
                                         transit_mode ='subway',
                                         departure_time = departure_time)

def stationEntrancestoStation(subwayStations):
    '''Map subwaystation entrance data to unique subway names'''
    stairInfo = {}
    for i, station in enumerate(subwayStations['stations']):
        #print('Processing station %s, %s' % (i, station['name']))
        googleInfo = googlePlacesNearestSubway(station['latitude'],
                                               station['longitude'])
        if googleInfo:
            print('Found station %s: %s' % (googleInfo.name, station['name']))
            stairInfo[station['name']] = {}
            stairInfo[station['name']]['stationName'] = googleInfo.name
            stairInfo[station['name']]['staionLat'] = googleInfo.geo_location['lat']
            stairInfo[station['name']]['staionLng'] = googleInfo.geo_location['lng']
    return stairInfo

def getClosestStation(lat, lon, subwayStations):
    '''Find the closest station to a given lat/lon'''
    stationsdistances = {}
    for station in subwayStations['stations']:
        stationsdistances[station['name']] = \
            geocalc(lat, lon, float(station['latitude']),
                                float(station['longitude']))
    return min(stationsdistances, key=stationsdistances.get)

def getClosestStations(df, stairInfo):
    '''Find the closest station for each listing in a dataframe'''
    #stationColumns = map(lambda x: x['name'], subwayStations['stations'])
    df['nearestStair'] = df[stairInfo.keys()].idxmin(axis=1)
    df['nearestStation'] = df['nearestStair'].apply(lambda x: stairInfo[x]['stationName'])
