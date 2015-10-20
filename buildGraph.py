import datetime
import networkx
from pandas import read_csv


def get_tripStops(tripID):
    tripTimes = times[times.trip_id == tripID]
    return tripTimes.merge(stops)[['departure_time', 'stop_lat',
                                   'stop_lon', 'stop_name',
                                   'stop_id']].sort('departure_time')


def parse_departure_time(x):
    return datetime.datetime.strptime(x['departure_time'], '%H:%M:%S')


def make_graph(tripIDs):
    graph = networkx.MultiDiGraph()
    for tripID in tripIDs:
        tripStops = get_tripStops(tripID)
        stopGenerator = tripStops.iterrows()
        lastStop = stopGenerator.next()[1]
        for index, thisStop in stopGenerator:
            timedelta = parse_departure_time(thisStop) - \
                        parse_departure_time(lastStop)
            minutes = timedelta.total_seconds() / 60.
            graph.add_edge(lastStop['stop_id'], thisStop['stop_id'],
                           key=tripID,
                           weight=minutes)
            graph.node[lastStop['stop_id']]['name'] = lastStop['stop_name']
            graph.node[lastStop['stop_id']]['lat'] = lastStop['stop_lat']
            graph.node[lastStop['stop_id']]['lon'] = lastStop['stop_lon']
            graph.node[thisStop['stop_id']]['name'] = thisStop['stop_name']
            graph.node[thisStop['stop_id']]['lat'] = thisStop['stop_lat']
            graph.node[thisStop['stop_id']]['lon'] = thisStop['stop_lon']

            lastStop = thisStop
    return graph


def gettripIds(index=0):
    tripIDs = []
    # For each route,
    for routeID, routeTrips in weekdayTrips.groupby('route_id'):
        # Pick a trip
        tripIDs.append(routeTrips.trip_id.values[index])
    return tripIDs

if __name__ == "__main__":

    calendar = read_csv('subwaydata/google_transit/calendar.txt')
    routes = read_csv('subwaydata/google_transit/routes.txt')
    trips = read_csv('subwaydata/google_transit/trips.txt')
    times = read_csv('subwaydata/google_transit/stop_times.txt')
    stops = read_csv('subwaydata/google_transit/stops.txt')

    weekdayServiceIDs = filter(lambda x: x.endswith('WKD'),
                               calendar.service_id)
    routeNameByID = {x['route_id']:
                     x['route_long_name'] for index, x in routes.iterrows()}
    weekdayTrips = trips[trips.service_id.isin(weekdayServiceIDs)]
    print(len(weekdayTrips))
    weekdayTimes = times[times.trip_id.isin(weekdayTrips.trip_id.unique())]

    tripIDs = gettripIds()
    graph = make_graph(tripIDs)
    import util
    util.pickle_save(graph, 'subwaydata/NYCsubway_network_graph.pkl')
