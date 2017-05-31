from slackclient import SlackClient
import urllib
import serial
import sys
from gps_data import gps_data
import time
from collections import deque
import Utils
import math
from geopy import distance
import sqlite3


slack_token = "YOUR_BOTS_TOKEN"

master_name = "aname"
master_first = "first_name"
master_last = "last_name"
master_id = 0

verbose_channel_name = "telemetry"
verbose_channel_id = 0
general_channel_name = "mrl"
general_channel_id = 0

sc = SlackClient(slack_token)

conn = sqlite3.connect("replied.sqlite")

COM_BAUD = 57600

TIMEOUT_MILLIS = 60000

GPS_TOLERANCE = 50

dataHeaders = [
    ["time", "date", "fix", "fixquality"],
    ["time", "date", "fix", "fixquality", "latitude", "longitude", "speed", "angle", "altitude", "satellites"]
]

latestData = deque()

gps_status = None

nice = dict()

def slack_connected():
    try:
        urllib.request.urlopen("http://api.slack.com")
        return True
    except urllib.error.URLError as err:
        return False

def send_verbose_slack(str):

    sc.api_call(
        "chat.postMessage",
        as_user=True,
#        channel="#bot_testing",
        channel=verbose_channel_id,
        text=str
    )

def send_master_slack(str):

    sc.api_call(
        "chat.postMessage",
        as_user=True,
        channel="@" + master_name,
        text=str
    )

def send_public_slack(str):

    sc.api_call(
        "chat.postMessage",
        as_user=True,
        channel= general_channel_id,  # "#" + general_channel_name,
        text=str
    )

def add_all_verbose_messages_to_db():
    messages = sc.api_call(
        "channels.history",
        channel=verbose_channel_id,
        count = 10,
    )

    if "error" in messages:
        messages = sc.api_call(
            "groups.history",
            channel=verbose_channel_id,
            count=10,
        )

    cursor = conn.cursor()
    for message in messages["messages"]:
        if message["type"] == "message":

            row = cursor.execute("SELECT * FROM messages WHERE ts like '{time}'".format(time = message["ts"]))

            if row.rowcount <= 0:
                # add the current message to the database

                cursor.execute("INSERT INTO messages VALUES (?)", [message["ts"]])
                conn.commit()

def get_command_from_master():

    messages = sc.api_call(
        "channels.history",
        channel=verbose_channel_id,
        count = 10,
    )

    if "error" in messages:
        messages = sc.api_call(
            "groups.history",
            channel=verbose_channel_id,
            count=10,
        )

    cursor = conn.cursor()
    for message in messages["messages"]:
        if message["type"] == "message":

            row = cursor.execute("SELECT * FROM messages WHERE ts like \"{time}\"".format(time = message["ts"])).fetchall()



            if len(row) <= 0:
                # add the current message to the database

                cursor.execute("INSERT INTO messages VALUES (?)", [message["ts"]])
                conn.commit()

                if message["user"] == master_id:
                    return message["text"]

def parse_gps(str):

    split = str.split(",")

    gps = None

    for i in range(0, len(dataHeaders)):
        if len(split) == len(dataHeaders[i]):
            for j in range(0, len(split)):
                nice[dataHeaders[i][j]] = split[j]
            try:
                gps = gps_data()
                gps.fromDict(nice)
            except:
                gps = None

            break

    return gps

def calcStdDev(gpsQueue):

    first = gpsQueue[0]

    average_lat  = 0
    average_long = 0

    for gps in gpsQueue:
        average_lat  += gps.getLatitude()
        average_long += gps.getLongitude()

    average_long = average_long / len(gpsQueue)
    average_lat = average_lat / len(gpsQueue)

    gps_average = gps_data()

    gps_average.setLatitude(average_lat)

    gps_average.setLongitude(average_long)

    distanceSum = 0



    for i in range(1, len(gpsQueue)):
        loc1_tuple = (gpsQueue[i].getLongitude(),gpsQueue[i].getLatitude())
        loc2_tuple = (gps_average.getLongitude(),gps_average.getLatitude())
        distanceSum += distance.distance(loc1_tuple, loc2_tuple).meters
#        distanceSum += Utils.calcGpsDistance(gps_average, gpsQueue[i]) ** 2

    distanceVariation = distanceSum / len(gpsQueue)

    return math.sqrt(distanceVariation)


def main():

    comport = input("Enter COM port name: ")

    global master_name
    global master_first
    global master_last
    global master_id
    global verbose_channel_name
    global verbose_channel_id
    global general_channel_name
    global general_channel_id

    master_name = input("Enter your slack username: ")

    print("Waiting for slack connection...")

    while not slack_connected():
        continue

    print("Connected!")

    info = sc.api_call(
        "users.list"
    )

    for user in info["members"]:
        if user["name"] == master_name:
            master_id = user["id"]
            master_first = user["profile"]["first_name"]

    send_master_slack("Hi " + master_first + "! Let's launch a rocket! :rocket:")

    info = sc.api_call(
        "channels.list"
    )

    for channel in info["channels"]:
        if channel["name"] == verbose_channel_name:
            verbose_channel_id = channel["id"]
        if channel["name"] == general_channel_name:
            general_channel_id = channel["id"]

    info = sc.api_call(
        "groups.list"
    )

    for channel in info["groups"]:
        if channel["name"] == verbose_channel_name:
            verbose_channel_id = channel["id"]
        if channel["name"] == general_channel_name:
            general_channel_id = channel["id"]

    c = conn.cursor()

    c.execute(
        '''DROP TABLE IF EXISTS messages''')

    conn.commit()

    c.execute(
        '''CREATE TABLE IF NOT EXISTS messages (
            ts TEXT UNIQUE
        )''')

    conn.commit()

    add_all_verbose_messages_to_db()

    # Open COM channel
    ser = serial.Serial(comport, COM_BAUD, timeout = 0, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, xonxoff=1)

    sc.api_call(
        "users.setPresence",
        presence="auto"
    )

    print("Listening... Further updates will be posted to Slack.")

    curLine = ""

    gps_status = None

    last_rec_time = time.time() * 1000

    alerted = False
    landed_alerted = False
    launch_alerted = False

    gps_start = None

    last_message_check = time.time() * 1000
    MESSAGE_CHECK_ITER = 5000

    message = ""

    maximum_altitude = 0
    maximum_speed = 0

    # Loop here and read COM data
    while True:

        if  time.time() * 1000 - last_message_check > MESSAGE_CHECK_ITER:
            message = get_command_from_master()
            last_message_check = time.time() * 1000

        if message == ".ready":
            if gps_status == None:
                send_verbose_slack("I haven't received GPS location yet! Can't Ready!")
            else:
                landed_alerted = False
                gps_start = gps_status
                gmaps_link = gps_status.getGoogleMapsLink()
                send_verbose_slack("Using current location as launch area: " + gmaps_link)

        if message == ".update":
            if gps_status == None:
                send_verbose_slack("I haven't recieved the rocket's position yet.")
            else:
                gmaps_link = gps_status.getGoogleMapsLink()
                send_verbose_slack("Hi " + master_first + ", the rocket is here: " + gmaps_link)
                send_public_slack("Updated rocket location: " + gmaps_link)

        if message == ".stats":
            if gps_start == None:
                send_verbose_slack("You must .ready before getting stats on the flight!")
            else:
                maximum_AGL = round(maximum_altitude - gps_start.getAltitude(), 2)
                maximum_speed_mph = round(maximum_speed * 1.151, 2)
                maximum_AMSL_feet = round(maximum_altitude * 3.28, 2)
                maximum_AGL_feet = round(maximum_AGL * 3.28, 2)
                send_verbose_slack("Some stats on the flight:"
                                   "\nMaximum SOG : {speed} knots ({speed_mph} mph)"
                                   "\nMaximum Altitude AGL : {altitude} m ({feet_altitude} ft)"
                                   "\nMaximum Altitude AMSL : {altitude_sea} m ({feet_altitude_sea} ft)"
                                   .format(speed=maximum_speed,
                                           speed_mph=maximum_speed_mph,
                                           altitude=maximum_AGL,
                                           feet_altitude=maximum_AGL_feet,
                                           altitude_sea=maximum_altitude,
                                           feet_altitude_sea=maximum_AMSL_feet))
        if message == ".forcelaunch":
            launch_alerted = True
            gps_start = gps_status
            send_verbose_slack("Launch forced!")

        message = ""

        bs = ser.read().decode("UTF-8")
        out = str(bs)
        if not out == '':
            if out == '\r':
                out = '\n'

        curLine += out

        if out == '\n':
            new_status = parse_gps(curLine)
            curLine = ""

            if not new_status == None and new_status.getLocationSet():
                if gps_status == None or alerted:
                    gmaps_link = new_status.getGoogleMapsLink()
                    send_verbose_slack("I have a lock on the rocket! " + gmaps_link)
                gps_status = new_status
                last_rec_time = time.time() * 1000
                if gps_status.getAltitude() > maximum_altitude:
                    maximum_altitude = gps_status.getAltitude()
                if gps_status.getSpeed() > maximum_speed:
                    maximum_speed = gps_status.getSpeed()

                alerted = False
                if launch_alerted:
                    if len(latestData) >= 20:
                        latestData.pop()
                    latestData.appendleft(gps_status)
                    gpsStdDev = calcStdDev(latestData)
                    print("Standard Deviation: " + str(gpsStdDev))
                    if gpsStdDev < 0.75 and not landed_alerted and len(latestData) >= 20 and gps_status.getSpeed() < 5:
                        gmaps_link = gps_status.getGoogleMapsLink()
                        send_public_slack("It looks like you landed!: " + gmaps_link)
                        landed_alerted = True
                        maximum_AGL = round(maximum_altitude - gps_start.getAltitude(),2)
                        maximum_speed_mph = maximum_speed * 1.151
                        maximum_AMSL_feet = round(maximum_altitude * 3.28,2)
                        maximum_AGL_feet = round(maximum_AGL * 3.28,2)
                        send_public_slack("Some stats on the flight:"
                                           "\nMaximum SOG : {speed} knots ({speed_mph} mph)"
                                           "\nMaximum Altitude AGL : {altitude} m ({feet_altitude} ft)"
                                           "\nMaximum Altitude AMSL : {altitude_sea} m ({feet_altitude_sea} ft)"
                                           .format(speed = maximum_speed,
                                                   speed_mph = maximum_speed_mph,
                                                   altitude = maximum_AGL,
                                                   feet_altitude = maximum_AGL_feet,
                                                   altitude_sea=maximum_altitude,
                                                   feet_altitude_sea = maximum_AMSL_feet))

        if time.time() * 1000 - last_rec_time > TIMEOUT_MILLIS and gps_status != None and not alerted:
            gmaps_link = gps_status.getGoogleMapsLink()
            send_verbose_slack("I haven't recieved anything in a while. Here's the last known location: " + gmaps_link)
            send_public_slack("I haven't recieved anything in a while. Here's the last known location: " + gmaps_link)
            alerted = True

        if gps_start != None and Utils.calcGpsDistance(gps_status, gps_start) >= GPS_TOLERANCE and not launch_alerted:
            gmaps_link = gps_status.getGoogleMapsLink()
            send_verbose_slack("We have liftoff! " + gmaps_link)
            launch_alerted = True

        sys.stdout.write(out)
        sys.stdout.flush()



if __name__ == '__main__':
    main()