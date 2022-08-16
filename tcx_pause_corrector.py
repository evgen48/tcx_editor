# importing element tree
import xml.etree.ElementTree as ET
import sys
from datetime import timedelta
import dateutil.parser
import matplotlib.pyplot as plt
import numpy as np

def calc_speed(x, y):
    v = []
    expected_pool_len = 25.0
    trackedDistance = 0
    npool = 0
    npooli = 0
    for i in range(0, len(x)):
        npoolNew = int(y[i] / expected_pool_len)
        # calculating speed  as constant for all points in between pool marks
        if npool != npoolNew:
            npool = npoolNew
            # speed in seconds per  100 m
            speed = 100 * (x[i] - x[npooli]) / expected_pool_len
            for j in range(npooli, i):
                v.append(speed)
                trackedDistance += 100 / speed
#                print(f"x={x[j]}, distance={trackedDistance}")

            npooli = i

    # last distance - floating point arith error accumulation
    missedDistance = y[len(y) - 1] - trackedDistance
    remainedLastSecondSpeed = 100 / missedDistance

    for i in range(0, len(x) - len(v)):
        v.append(remainedLastSecondSpeed)
        remainedLastSecondSpeed = 0

    return v

def apply_time_distance_data(root, x,y) :
    idx = 0
    startTime = 0
    for activities in root.findall(namespace + "Activities"):
        for activity in activities.findall(namespace + "Activity"):
            for lap in activity.findall(namespace + "Lap"):
                for Track in lap.findall(namespace + "Track"):
                    for TrackPoint in Track.findall(namespace + "Trackpoint"):
                        time = TrackPoint.find(namespace + "Time")
                        distance = TrackPoint.find(namespace + "DistanceMeters")
                        isotime = dateutil.parser.isoparse(time.text)

                        if idx == 0:
                            startTime = isotime.timestamp()

                        #time shift correction
                        ctime = isotime.timestamp() - startTime
                        diff = ctime - x[idx]
                        isotime -= timedelta(diff)
                        newtime = isotime.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
                       # TODO: fix that
                       # time.text = newtime

                        #distance set
                        if distance != None:
                            distance.text = str(y[idx])
                        else:
                            distance = ET.Element(namespace + "DistanceMeters")
                            distance.text = str(y[idx])
                            TrackPoint.append(distance)

                        idx += 1


filename = sys.argv[1]

# Pass the path of the xml document
namespace = "{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}"
ET.register_namespace("", "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2")
#xmlns="http://www.garmin.com/xmlschemas/ActivityExtension/v2"
tree = ET.parse(filename)


# get the parent tag
root = tree.getroot()

# print the root (parent) tag along with its memory location
print(root)

prevTime = None
accumulatedPause = None

x = []
y = []
prevDistance = 0
startTime = 0

for activities in root.findall(namespace + "Activities"):
     for activity in activities.findall(namespace + "Activity"):
         for lap in activity.findall(namespace + "Lap"):
             for Track in lap.findall(namespace + "Track") :
                 for TrackPoint in Track.findall(namespace + "Trackpoint"):
                     time = TrackPoint.find(namespace + "Time")
                     distance = TrackPoint.find(namespace + "DistanceMeters")

                     isotime = dateutil.parser.isoparse(time.text)
                     if startTime == 0:
                         startTime = isotime.timestamp()
                     x.append(isotime.timestamp() - startTime)
                     if distance != None :
                         fdistance = float(distance.text)
                         y.append(fdistance)
                         prevDistance = fdistance
                     else:
                         y.append(prevDistance)

                     if prevTime != None:
                        tdelta = isotime - prevTime
                        # pause threshold
                        if tdelta.seconds > 10:
                            if accumulatedPause != None:
                               accumulatedPause += tdelta
                            else:
                                accumulatedPause = tdelta
                            accumulatedPause -= timedelta(seconds=1)

                            print(f"Pause: {tdelta}")
                            print(f"Total: {accumulatedPause}")
                     prevTime = isotime

                     # adding necessary delta to timestamps so all pauses will be removed
                     if accumulatedPause != None:
                         isotime -= accumulatedPause
                         newtime = isotime.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]+"Z"
                         time.text = newtime




plt.style.use('_mpl-gallery')


# pause correction
x_corrected = []
y_corrected = []
timeGap = 0
x_corrected.append(x[0])
for i in range(1, len(x)):
    x_corrected.append(x[i] - timeGap)
    if x_corrected[i] - x_corrected[i-1] > 5:
        timeGap += x_corrected[i] - x_corrected[i-1] - 1
        x_corrected[i] = x_corrected[i-1] + 1





#v.append((y[i] - y[i-1]) / (x[i] - x[i-1]))

# plot
fig, ax = plt.subplots(2, 2)

plt.subplots_adjust(bottom=0.1, left=0.1, top=0.9)

fig.set_figwidth(8)
fig.set_figheight(6)

ax[0, 0].plot(x, y, linewidth=1.0, drawstyle='steps-post')

ax[0, 0].set_ylabel('distance, m')  # Add a y-label to the axes.
ax[0, 0].set_title("original data")  # Add a title to the axes.


# distance correction
speed_correction = calc_speed(x_corrected, y)
y_corrected = []
y_corrected.append(0)

for i in range(1, len(x)):
    if speed_correction[i-1] != 0:
        y_corrected.append(y_corrected[i-1] + 100 / speed_correction[i-1])
    else:
        y_corrected.append(y_corrected[i - 1])

#    print(f"XML: t={x_corrected[i]}, distance={y_corrected[i]}")


ax[1, 0].plot(x, calc_speed(x, y), linewidth=1.0)
ax[1, 0].set(ylim=(60, 150))
ax[1, 0].set_xlabel('time, sec')  # Add an x-label to the axes.
ax[1, 0].set_ylabel('speed, sec/100m')  # Add a y-label to the axes.





ax[0, 1].plot(x_corrected, y, linewidth=1.0)
ax[0, 1].plot(x_corrected, y_corrected, linewidth=1.0, color='red')
ax[0, 1].set_title("pauses, speed - corrected")  # Add a title to the axes.

ax[1, 1].plot(x_corrected, calc_speed(x_corrected, y), linewidth=1.0)
ax[1, 1].set(ylim=(60, 150))
ax[1, 1].set_xlabel('time, sec')  # Add an x-label to the axes.



#applying time distance correction
apply_time_distance_data(root, x_corrected, y_corrected)
tree.write(filename + ".tcx")


plt.show()