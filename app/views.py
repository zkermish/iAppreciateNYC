from flask import render_template, request, Response, jsonify
from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map

from app import app
import pymysql as mdb
from a_Model import ModelIt
import pygal
import numpy as np

GoogleMaps(app)

@app.route('/index')
def index():
    return render_template("index.html",
        title = 'Home', user = { 'nickname': 'Miguel' },
        )


@app.route("/db_fancy")
def cities_page_fancy():
    db = mdb.connect(user="root", host="localhost", db="world_innodb",  charset='utf8')

    with db:
        cur = db.cursor()
        cur.execute('SELECT Name, CountryCode, \
            Population FROM City ORDER BY Population LIMIT 15;')

        query_results = cur.fetchall()
    cities = []
    for result in query_results:
        cities.append(dict(name=result[0], country=result[1], population=result[2]))
    return render_template('cities.html', cities=cities)

@app.route('/')
@app.route('/input')
def cities_input():
    return render_template("input.html")

@app.route('/output')
def cities_output():

    #pull 'ID' from input field and store it
    address = request.args.get('ID')

    import util
    import distances
    import getGeocodes
    subwayStations = util.pickle_load('/var/www/iAppreciateNYC/subwaydata/NYCsubway_network.pkl')
    stairInfo = util.pickle_load('/var/www/iAppreciateNYC/subwaydata/NYCsubway_network_withUnique3.pkl')
    geoObj = getGeocodes.getGeoObj(address)
    closestStair = distances.getClosestStation(geoObj.latitude,
                                               geoObj.longitude,
                                               subwayStations)
    closestStation = stairInfo[closestStair]['stationName']
    mymap = Map(
        identifier="view-side",
        lat=geoObj.latitude,
        lng=geoObj.longitude,
        markers=[(geoObj.latitude, geoObj.longitude)],
        zoom=15
    )

    mydb = mdb.connect(user="root", host="localhost",
                       db="iapp",  charset='utf8')
    with mydb:
        cur = mydb.cursor()
        #just select the city from the world_innodb that the user inputs
        cur.execute("SELECT sellData, `%s` FROM stationPPSFT;" % closestStation[:60])
        query_results = cur.fetchall()

    sellDate1, ppsqf = zip(*query_results)
    with mydb:
        cur = mydb.cursor()
        #just select the city from the world_innodb that the user inputs
        resultTable = closestStation+'_GPprediction'
        cur.execute("SELECT sellData, `%s`, pred, sigma FROM `%s`;" %
                    (closestStation[:60]+'_filtered', resultTable))
        query_results = cur.fetchall()

    sellDate2, smoothed, pred, sigma = zip(*query_results)

    #line_chart = pygal.Line(disable_xml_declaration=True, x_label_rotation=20)
    #line_chart.title = 'Price per square foot appreciation'
    #line_chart.x_labels =  map(lambda d: d.strftime('%Y-%m-%d'), list(sellDate1))
    #line_chart.add(closestStation, list(ppsqf))

    dateline = pygal.DateLine(disable_xml_declaration=True,
                                  x_label_rotation=25)
    dateline.add(closestStation, zip(sellDate1, ppsqf))
    dateline.add('Filtered', zip(sellDate2, smoothed))
    dateline.add('Forecast', zip(sellDate2, pred))
    upperBound = (np.array(pred, dtype=np.float) +
                            1.96*np.array(sigma, dtype=np.float))
    lowerBound = (np.array(pred, dtype=np.float) -
                            1.96*np.array(sigma, dtype=np.float))
    dateline.add('Bound', zip(np.array(sellDate2)[np.isfinite(upperBound)], upperBound[np.isfinite(upperBound)]))
    dateline.add('Bound', zip(np.array(sellDate2)[np.isfinite(lowerBound)], lowerBound[np.isfinite(lowerBound)]))

    cities = []
    #for result in query_results:
    #    cities.append(dict(name=result[0], country=result[1], population=result[2]))
    #call a function from a_Model package. note we are only pulling one result in the query
    #pop_input = cities[0]['population']
    #the_result = ModelIt(city, pop_input)
    return render_template("output.html",
							cities=cities,
                            stair = closestStair,
                            station=closestStation,
                            mymap=mymap,
                            line_chart = dateline)

@app.route('/linechart/')
def linechart():
    line_chart = pygal.Line()
    line_chart.title = 'Browser usage evolution (in %)'
    line_chart.x_labels = map(str, range(2002, 2013))
    line_chart.add('Firefox', [None, None, 0, 16.6, 25, 31, 36.4, 45.5, 46.3, 42.8, 37.1])
    line_chart.add('Chrome', [None, None, None, None, None, None, 0, 3.9, 10.8, 23.8, 35.3])
    line_chart.add('IE', [85.8, 84.6, 84.7, 74.5, 66, 58.6, 54.7, 44.8, 36.2, 26.6, 20.1])
    line_chart.add('Others', [14.2, 15.4, 15.3, 8.9, 9, 10.4, 8.9, 5.8, 6.7, 6.8, 7.5])
    return Response(response=line_chart.render(), content_type='image/svg+xml')

@app.route("/maps")
def mapview():
    # creating a map in the view
    mymap = Map(
        identifier="view-side",
        lat=37.4419,
        lng=-122.1419,
        markers=[(37.4419, -122.1419)]
    )
    sndmap = Map(
        identifier="sndmap",
        lat=37.4419,
        lng=-122.1419,
        markers={'http://maps.google.com/mapfiles/ms/icons/green-dot.png':[(37.4419, -122.1419)],
                 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png':[(37.4300, -122.1400)]}
    )
    return render_template('googlemap.html', mymap=mymap, sndmap=sndmap)
