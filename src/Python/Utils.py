from gps_data import gps_data
from geopy import distance

# Diameter of Earth in meters
EARTH_RADIUS = 6371000

def calcGpsDistance(g1, g2):

    loc_1 = (g1.getLatitude(), g1.getLongitude())
    loc_2 = (g2.getLatitude(), g2.getLongitude())

    return distance.distance(loc_1, loc_2).meters
