import numpy as np
import time
from urllib2 import URLError
import networkx


def geocalc(lat0, lon0, lat1, lon1):
    """Return the distance (in km) between two points in
    geographical coordinates."""
    EARTH_R = 6372.8

    lat0 = np.radians(lat0)
    lon0 = np.radians(lon0)
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    dlon = lon0 - lon1
    y = np.sqrt((np.cos(lat1) * np.sin(dlon)) ** 2 +
                (np.cos(lat0) * np.sin(lat1) -
                 np.sin(lat0) * np.cos(lat1) * np.cos(dlon)) ** 2)
    x = np.sin(lat0) * np.sin(lat1) + \
        np.cos(lat0) * np.cos(lat1) * np.cos(dlon)
    c = np.arctan2(y, x)
    return EARTH_R * c


def getStationDistancesGraph(df, graph):
    '''Use the subway network graph to get distances between stations'''
    for i, station in enumerate(graph.nodes()):
        node = graph.node[station]
        print('On station %s: %s' % (i, node['name']))
        df[station] = \
            df['geoObj'].apply(lambda x: geocalc(x.latitude, x.longitude,
                                                 float(node['lat']),
                                                 float(node['lon'])))


def getClosestStationsGraph(df, graph):
    '''Find the closest station for each listing in a dataframe'''
    df['nearestStation'] = df[graph.nodes()].idxmin(axis=1)
    df['nearestStationName'] = \
        df['nearestStation'].apply(lambda x: graph.node[x]['name'])


def getClosestStationGraph(lat, lon, graph):
    '''Find the closest station to a given lat/lon'''
    stationsdistances = {}
    for station in graph.nodes():
        node = graph.node[station]
        stationsdistances[station] = \
            geocalc(lat, lon, float(node['lat']), float(node['lon']))
    return min(stationsdistances, key=stationsdistances.get)


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


def timeoutSafeQuery(google_places, params):
    try:
        query_result = google_places.nearby_search(**params)
        print('Yeah')
        return query_result
    except URLError:
        print('URLError. Waiting...')
        time.sleep(2)
        timeoutSafeQuery(google_places, params)


def googlePlacesNearestSubway(lat, lon, radius=600):
    from googleplaces import GooglePlaces, types, lang
    import credentials
    google_places = GooglePlaces(credentials.google_key)
    params = {'lat_lng': {'lat': lat, 'lng': lon},
              'radius': radius,
              'types': [types.TYPE_SUBWAY_STATION],
              'rankby': 'distance'}
    query_result = timeoutSafeQuery(google_places, params)
    try:
        return query_result.places[0]
    except IndexError:
        print('No subway nearby?')
        return None


def googleMapsTransitTimes(stairInfo):
    departure_time = datetime.datetime(2015, 9, 14, 9, 0, 0)
    directions_result = gmaps.directions(origin, destination, mode='transit',
                                         transit_mode='subway',
                                         departure_time=departure_time)


def addStationNamestoGraph(graph):
    for node in graph.nodes():
        try:
            googleInfo = googlePlacesNearestSubway(graph.node[node]['lat'],
                                                   graph.node[node]['lon'])
        except KeyError:
            print('No lat/lon for %s' % node)
            continue
        if googleInfo:
            print('Found station %s: %s' % (googleInfo.name, graph.node[node]))
            stationName = googleInfo.name
            graph.node[node]['name'] = stationName
        else:
            print('No station found nearby %s?' % station['name'])
        return graph


def stationEntrancestoStation(subwayStations):
    '''Map subwaystation entrance data to unique subway names
    (appending) lines running at station to disambguiate repeated names'''
    stairInfo = {}

    for i, station in enumerate(subwayStations['stations']):
        # print('Processing station %s, %s' % (i, station['name']))
        googleInfo = googlePlacesNearestSubway(station['latitude'],
                                               station['longitude'])
        if googleInfo:
            print('Found station %s: %s' % (googleInfo.name, station['name']))
            stationName = googleInfo.name
            for line in station['lines']:
                stationName += ('_%s' % line['line_id'])
            stairInfo[station['name']] = {}
            stairInfo[station['name']]['stationName'] = stationName
            stairInfo[station['name']]['stationLat'] = googleInfo.geo_location['lat']
            stairInfo[station['name']]['stationLng'] = googleInfo.geo_location['lng']
        else:
            print('No station found nearby %s?' % station['name'])
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
    # stationColumns = map(lambda x: x['name'], subwayStations['stations'])
    df['nearestStair'] = df[stairInfo.keys()].idxmin(axis=1)
    df['nearestStation'] = df['nearestStair'].apply(lambda x: stairInfo[x]['stationName'])


def getLinegraph(routeID='L'):
    print(routeNameByID[routeID])
    routeWeekdayTrips = weekdayTrips[weekdayTrips.route_id == routeID]
    stopIDs = routeWeekdayTrips.merge(weekdayTimes)
    stops[stops.stop_id.isin(stopIDs)].stop_name.unique()
    tripIds = stopIDs.trip_id.unique()
    graph = make_graph([tripIds[0]])
    graph = addStationNamestoGraph(graph)
    return graph


def getMappings(graph):
    mapFromId = networkx.get_node_attributes(graph, 'name')
    mapToId = {v: k for k, v in mapFromId.items()}
    return mapFromId, mapToId
