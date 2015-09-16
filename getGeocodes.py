import geopy
import time

from geopy.geocoders import Nominatim
from geopy.geocoders import GoogleV3
from geopy.geocoders.base import GeocoderTimedOut
from geopy.geocoders.base import SSLError
import util
from credendials import google_key

GOOGgeolocator = GoogleV3(api_key=google_key)

# google geolocator would have worked as is, but i can do a mapping
# workarond to use OSM
#155 East 93rd Street ,  Manhattan, NY
#Lat/Long = (40.7837631, -73.9517633)

OSMgeolocator = Nominatim()

def getGeoObj(address, waitTime=1.01,  numTries = 0):
    time.sleep(waitTime)
    print(address)
    try:
        location = OSMgeolocator.geocode(address)
    except (GeocoderTimedOut, SSLError):
        #print('Using google. Watch out for limits!')
        #location = GOOGgeolocator.geocode(address)
        numTries += 1
        print('Timed out %s times, try again' % numTries)
        if numTries < 3:
            return getGeoObj(address, waitTime, numTries)
        else:
            print('Using google. Watch out for limits!')
            location = GOOGgeolocator.geocode(address)
    if location is None:
        print('Using google. Watch out for limits!')
        location = GOOGgeolocator.geocode(address)

    print('Lat/Long = (%s, %s)' % (location.latitude, location.longitude))
    return location
