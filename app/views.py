from flask import render_template, request, Response, jsonify
from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map

from app import app
import pymysql as mdb
from a_Model import ModelIt
import pygal
import numpy as np

GoogleMaps(app)


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route("/db_fancy")
def cities_page_fancy():
    db = mdb.connect(user="root", host="localhost",
                     db="world_innodb",  charset='utf8')

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
    from datetime import date

    #graph = util.pickle_load('/var/www/iAppreciateNYC/subwaydata/NYCsubway_network_graph_9-28.pkl')
    graph = util.pickle_load('subwaydata/NYCsubway_network_graph_9-28.pkl')
    geoObj = getGeocodes.getGeoObj(address)
    closestStation = distances.getClosestStationGraph(geoObj.latitude,
                                                      geoObj.longitude,
                                                      graph)

    closestStationName = graph.node[closestStation]['name']

    mymap = Map(
        identifier="view-side",
        lat=geoObj.latitude,
        lng=geoObj.longitude,
        markers=[(geoObj.latitude, geoObj.longitude)],
        zoom=15
    )

    mydb = mdb.connect(user="root", host="localhost",
                       db="iapp2",  charset='utf8')
    with mydb:
        cur = mydb.cursor()
        cur.execute("SELECT sellData, `%s` FROM stationPPSFT2;" %
                    closestStation[:60])
        query_results = cur.fetchall()

    sellDate1, ppsqf = zip(*query_results)
    with mydb:
        cur = mydb.cursor()
        resultTable = closestStation+'_GPprediction'
        cur.execute("SELECT sellData, `%s`, y_pred, sigma_pred FROM `%s`;" %
                    (closestStation[:60]+'_filtered', resultTable))
        query_results = cur.fetchall()

    sellDate2, smoothed, pred, sigma = zip(*query_results)

    from pygal.style import Style
    custom_style = Style(label_font_size=16, major_label_font_size=16,
                         colors=('#ff1100', '#E89B53', '#0000ff',
                                 '#E89B53', '#E89B53'))

    dateline = pygal.DateLine(disable_xml_declaration=True,
                              x_label_rotation=25,
                              x_title='Date',
                              y_title='Price per square foot',
                              style=custom_style,
                              show_x_guides=True,
                              show_legend=False)
    dateline.x_labels = [date(2008, 1, 1), date(2010, 1, 1),
                         date(2012, 1, 1), date(2014, 1, 1), date(2016, 1, 1),
                         date(2018, 1, 1), date(2020, 1, 1)]

    dateline.add(closestStation, zip(sellDate1, ppsqf))
    dateline.add('Forecast', zip(sellDate2, pred), show_dots=False,
                 stroke_style={'width': 5})
    dateline.add('Filtered', zip(sellDate2, smoothed), show_dots=False,
                 stroke_style={'width': 5})
    upperBound = (np.array(pred, dtype=np.float) +
                  1.96*np.array(sigma, dtype=np.float))
    lowerBound = (np.array(pred, dtype=np.float) -
                  1.96*np.array(sigma, dtype=np.float))
    dateline.add('Bound', zip(np.array(sellDate2)[np.isfinite(upperBound)],
                 upperBound[np.isfinite(upperBound)]),
                 stroke_style={'width': 5,
                 'dasharray': '3, 6, 12, 24'},
                 show_dots=False)
    dateline.add('Bound', zip(np.array(sellDate2)[np.isfinite(lowerBound)],
                 lowerBound[np.isfinite(lowerBound)]),
                 stroke_style={'width': 5,
                 'dasharray': '3, 6, 12, 24'},
                 show_dots=False)

    return render_template("output.html",
                           address=address,
                           station=closestStationName,
                           mymap=mymap,
                           line_chart=dateline)

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
