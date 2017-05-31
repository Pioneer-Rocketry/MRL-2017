
DEF_LAT = 1
DEF_LONG = -1



GMAPS_STRING = "https://www.google.com/maps?q="

class gps_data(object):

    def __init__(self):
        self.latitude = 0
        self.longitude = 0
        self.time = 0
        self.fix = False
        self.quality = 0
        self.speed = 0
        self.angle = 0
        self.altitude = 0
        self.satellites = 0
        self.date = 0
        self.lat_mult = DEF_LAT
        self.long_mult = DEF_LONG
        self.locationSet = False

    def setLatitude(self, lat):

        if isinstance(lat, str):
            formatted = lat[:2] + "." + lat[2:]
            self.latitude = float(formatted)
        else:
            self.latitude = lat

        self.locationSet = True

    def setLongitude(self, long):

        if isinstance(long, str):
            formatted = long[:2] + "." + long[2:]
            self.longitude = float(formatted)
        else:
            self.longitude = long

        self.locationSet = True

    def setTime(self, t):
        self.time = t

    def setDate(self, date):
        self.date = date

    def setFix(self, f):

        f = int(f)

        if f == 1:
            self.fix = True
        else:
            self.fix = False

    def setFixQuality(self, q):
        self.quality = int(q)

    def setSpeed(self, s):
        self.speed = float(s)

    def setAngle(self, a):
        self.angle = float(a)

    def setAltitude(self, a):
        self.altitude = float(a)

    def setSatellites(self, s):
        self.satellites = int(s)

    def getLatitude(self):
        return self.latitude

    def getLongitude(self):
        return self.longitude

    def getTime(self):
        return self.time

    def getFix(self):
        return self.fix

    def getFixQuality(self):
        return self.quality

    def getSpeed(self):
        return self.speed

    def getAngle(self):
        return self.angle

    def getAltitude(self):
        return self.altitude

    def getSatellites(self):
        return self.satellites

    def getGoogleMapsLink(self):
        return GMAPS_STRING + str(self.latitude * self.lat_mult) + "," + str(self.longitude * self.long_mult)

    def getDistance(self, gps2):

        long2 = gps2.getLongitude()
        lat2  = gps2.getLatitude()

    def getLocationSet(self):

        return self.locationSet




    def fromDict(self, d):

        for key, value in d.items():
            print(key + ", " + value)

            if key == "time":
                self.setTime(value)
            elif key == "date":
                self.setDate(value)
            elif key == "fix":
                self.setFix(value)
            elif key == "fixquality":
                self.setFixQuality(value)
            elif key == "latitude":
                self.setLatitude(value)
            elif key == "longitude":
                self.setLongitude(value)
            elif key == "latitude":
                self.setLatitude(value)
            elif key == "speed":
                self.setSpeed(value)
            elif key == "angle":
                self.setAngle(value)
            elif key == "altitude":
                self.setAltitude(value)
            elif key == "satellites":
                self.setSatellites(value)




