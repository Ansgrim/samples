"""
Team crash.py
Project 4 Capture the Flag Agent
5/1/18

Agent that attempts to play capture the flag based on the project description
"""
from Mambo import Mambo
import math
from DroneVisionGUI import DroneVisionGUI
import pickle
import os
import time
from ar_markers import detect_markers
import serial
import os

whiffcount = 0          #tracks the number of frames drone does not see any markers
lastmarker = 999        #last known location marker - initialized to arbitrary number
lastmidmarker = 99      #last known mid-level marker - initialized to arbitrary number
basemarker = 62         #location marker tied to our base
enemyflag = -1          #location marker of enemy flag - starts at -1
enemybase = -1          #location marker of enemy base - starts at -1
carryingflag = False    #tracking whether flag is being carried
taglockouts = []        #tracking ids for tag lockouts
tagtimes = []           #tracking times for tag lockouts - corresponds to same index in taglockouts
walldistance = 4        #tracking distance from the wall


start = -1      #start timer

zdir = 0    #tracking z-direction drone should be moving

scoreledger = 'scoreledger.txt'     #file for scoring

#if this file exists, then we know where the enemy flag is
if os.path.isfile('flagloc.pk'):
    #load in enemy base location
    with open('flagloc.pk', 'rb') as fi:
        enemyflag = int(pickle.load(fi))
if enemyflag < 0 or enemyflag > 500:
    enemyflag = -1

#calculate the marker strings - these strings identify wall markers
    #format "N1.3" where N/E/S/W is wall marker is on
        #and number is distance from wall ccw to marker
markerStrings = ["" for x in range(100)]
for i in range(5, 100):
    if i <= 30:
        st = "N"
        dist = (i-4)*1.5
        st = st + str(dist)
        markerStrings[i] = st
    elif i <= 50:
        st = "E"
        dist = (i-30)*1.5
        st = st + str(dist)
        markerStrings[i] = st
    elif i <= 77:
        st = "S"
        dist = (i-51)*1.5
        st = st + str(dist)
        markerStrings[i] = st
    else:
        st = "W"
        dist = (i-77)*1.5
        st = st + str(dist)
        markerStrings[i] = st
print(markerStrings)

'''
    wallDistance calculates the distance of the drone is on the wall given the distance between the centers of two markers found
    Markers are known to be 1.5 ft apart.
    It's a linear relationship between distance in markers and distance from the wall, so this linear model should
        reasonably estimate the distance the drone is from the wall.
    Linear model was found by manually measuring the distance the drone was from the wall and calculating the pixel distance
        of 
    @param diff - distance between the centers of two markers
    @return - the estimated distance the drone is from the wall - want it to be between 2 and 4 meters
'''
def wallDistance(diff):
    return diff/-50 + 6.48    

#if true, actually runs the program - if false, just testing vision
testFlying = True


'''
    Core class for vision - contains the code to read markers
    Also contains the callback function
'''
class UserVision:
    '''
        Initializer - 
        @param vision - passes in vision parameter for sight
    '''
    def __init__(self, vision):
        self.index = 0
        self.vision = vision

    '''
        The Callback Function
        This is where all the vision is happening
        This function changes all global variables based on what markers are seen
    '''
    def marker_search(self, args):
        #tracking all global variables necessary
        global whiffcount
        global lastmarker
        global lastmidmarker
        global enemyflag
        global enemybase
        global carryingflag
        global taglockouts
        global tagtimes
        global walldistance
        global zdir
        global ser

        #get the picture
        img = self.vision.get_latest_valid_picture()

        #shouldnt fail, but checking if it failed anyway
        if (img is not None):
            #initialize counters for 400 and 200 nodes
            fourMarkers = 0
            twoMarkers = 0
            
            #find the markers - puts them into an array
            markers = detect_markers(img)
            
            #initialize search for finding our location based on mid markers and other markers
            highestmarker = 0
            highestmidmarker = 0
            
            #convert array of markers to array of marker IDs
            mids = []
            for marker in markers:
                mids.append(int(marker.id))
                marker.highlite_marker(img)
                
            #for every marker id...
            for mid in mids:
                #if we found one in the 400's that is a location marker
                if mid > 404 and mid < 500:
                    #increment that count
                    fourMarkers = fourMarkers + 1
                    #if this is the highest # marker we've seen, then save it
                    if mid % 100 > highestmarker % 100:
                        highestmarker = mid
                #if we found one in the 200's that is a location marker
                elif mid > 204 and mid < 300:
                    #increment that count
                    twoMarkers = twoMarkers + 1
                    #if this is the highest # marker we've seen, then save it
                    if mid % 100 > highestmarker % 100:
                        highestmarker = mid
                #if we found a mid-level wall marker
                elif mid < 100:
                    #and this is the new highest mid marker, save it
                    if mid > highestmidmarker:
                        highestmidmarker = mid
                #if we found another drone (WOW)
                elif (mid % 100 == 3 or mid % 100 == 4) and mid < 400:
                    #search for the id in taglockouts
                    ind = -1
                    for i in range(len(taglockouts)):
                        if taglockouts[i] == mid:
                            ind = i
                    #if we found it, check the time stamp
                    if ind >= 0:
                        #if it is too soon, skip this marker
                        if time.time() - tagtimes[ind] < 2:
                            continue
                        #otherwise remove it and keep going
                            taglockouts.remove(mid)
                            tagtimes.remove(tagtimes[ind])
                    #add the score to the ledger
                    f = open(scoreledger, 'a+')
                    f.write("found enemy " + str(mid) + ": +1 points " + str(time.time()) + "\n")
                    #and add the marker to the lockouts
                    taglockouts.append(mid)
                    tagtimes.append(time.time())
                #if we found our teammate (EVEN MORE WOW)
                elif (mid == 403):
                    #write that to the ledger too, i guess
                    f = open(scoreledger, 'a+')
                    f.write("tagged teammate\n")
                #if we found the enemy flag (!!!!!!!)
                elif mid % 100 == 2 and mid < 402:
                    #save location, play noise, and grab the flag
                    path = os.path.abspath('\FARTNoises\FART2.wav')
                    os.system('start %s' % path).play()
                    carryingflag = True
                    #if by some miracle this isnt the first time we grab the flag, we dont need to save the location
                    if enemyflag == -1 and lastmarker != 999:
                        enemyflag = lastmarker
                        #write results to file
                        with open('flagloc.pk', 'wb') as f:
                            pickle.dump(enemyflag, f)
                #if we found our base
                elif mid == 401:
                    #...and we have the flag
                    if carryingflag:
                        #SCORE! JACKPOT BABY
                        carryingflag = False
                        f = open(scoreledger, 'a+')
                        f.write("flag captured: +10 points " + str(time.time()) + "\n")
                        path = os.path.abspath('\FARTNoises\FART3.wav')
                    os.system('start %s' % path).play()
                #if we found the enemy base
                elif mid % 100 == 1:
                    #search for the id in taglockouts
                    ind = -1
                    for i in range(len(taglockouts)):
                        if taglockouts[i] == mid:
                            ind = i
                    #if we found it, check the time stamp
                    if ind >= 0:
                        #if it is too soon, skip this marker
                        if time.time() - tagtimes[ind] < 30:
                            continue
                        #otherwise remove it and keep going
                        else:
                            taglockouts.remove(mid)
                            tagtimes.remove(tagtimes[ind])
                    #add the score
                    f = open(scoreledger, 'a+')
                    f.write("enemy base tagged: +2 points " + str(time.time()) + "\n")
                    #and add the marker to the lockouts
                    taglockouts.append(mid)
                    tagtimes.append(time.time())
                    
            #so now that we parsed all the markers, we gotta figure out what to do with that info

            #if we found way more 400 markers than 200 markers
            if fourMarkers > twoMarkers + 1:
                #go down some
                zdir = 0
            #if we found way more 200 markers than 400 markers
            elif twoMarkers > fourMarkers + 1:
                #go up some
                zdir = 0
            #otherwise, keep it level (hopefully)
            else:
                zdir = 0

            #if we found a highestmarker, then we have our location
            #this wont happen every time, especially if we find no markers (which is not unlikely)
            if highestmarker != 0:
                #save it
                lastmarker = highestmarker
                #initialize centerpoints
                p1 = 0
                p2 = 0
                #search for the centers of this id and this id-1
                for m in markers:
                    if int(m.id) == lastmarker:
                        p1 = m.center
                    elif int(m.id) == lastmarker-1:
                        p2 = m.center
                #if we found one, then calculate wall distance
                if p2 != 0:
                    dist = math.sqrt((int(p1[0])-int(p2[0]))**2 + (int(p1[1])-int(p2[1]))**2)
                    walldistance = wallDistance(dist)
            
            #print location for testing purposes
            print("location: " + str(lastmarker) + "midloc: " + str(lastmidmarker) + "walldist: " + str(walldistance))
            
            #tell other drone where we are and where enemyflag is
            stng = str(lastmarker) + "," + str(enemyflag) + "\n"
            ser.write(str.encode(stng))

            #read in and parse info from other team
            serin = ser.readline()
            serial_input = serin.decode('utf-8')
            coord = serial_input.split(",")

            # if serial reads correctly and gets enemy flag location from other team
            if (len(coord) == 2):
                print("transmission: " + str(coord[0]) + "," + str(coord[1]))
                #if other team is close to us move forward a bit to avoid crashing
                if ((int(coord[0]) - lastmarker) < 5):
                    mambo.fly_direct(roll=0, pitch=7, yaw=0, vertical_movement=0, duration=.1)
            
                #if flag is still not found set it from other team
                if enemyflag == -1:
                    if (coord[1] != '-'):
                        enemyflag = int(coord[1])
                #if flag is found, write to file
                if enemyflag != -1:
                    with open('flagloc.pk', 'wb') as f:
                        pickle.dump(enemyflag, f)

            #if we found a highestmidmarker, then we have our mid marker location
            if highestmidmarker != 0:
                #save it
                lastmidmarker = highestmidmarker
            
            #if we missed a lot of markers, then increment the whiff counter
            if twoMarkers < 1 and fourMarkers < 1:
                whiffcount = whiffcount + 1
            else:
                whiffcount = 0
            #whiff counter currently unused, but may have use in being too far from the wall or something
                

'''
    getAngle - get the angle between the markers represented by the string
    String format example: "N3.5"
    N/E/S/W represents the wall the marker is on
    The number after the wall is the distance to the next nearest wall counterclockwise
        So for a node on the north wall, it is the distance to the west wall
    Function is dependent on the width and height of the room, given below
'''
width = 12*3.28084
height = 10*3.28084
def getAngle(start, end):
    swall = start[0]
    ewall = end[0]
    spos = float(start[1:])
    epos = float(end[1:])
    if(swall == ewall):            
        return 0
    if((swall == "N" and ewall == "S") or (swall == "S" and ewall == "N")):
        angle = 180/math.pi * math.atan((width-spos-epos)/height)
        if spos+epos > height:
            angle = angle * -1
        return angle
    elif((swall == "E" and ewall == "W") or (swall == "W" and ewall == "E")):
        angle = 180/math.pi * math.atan((height-spos-epos)/width)
        if spos+epos > width:
            angle = angle * -1
        return angle
    elif((swall == "N" and ewall == "E" ) or (swall == "S" and ewall == "W")):
        return -180/math.pi * math.atan((width-spos)/epos)  
    elif((swall == "E" and ewall == "S") or (swall == "W" and ewall == "N")):
        return -180/math.pi * math.atan((height-spos)/epos)
    elif((swall == "N" and ewall == "W") or (swall == "S" and ewall == "E")):
        return 180/math.pi * math.atan(spos/(height-epos))
    elif((swall == "E" and ewall == "N") or (swall == "W" and ewall == "S")):
        return 180/math.pi * math.atan(spos/(width-epos))
    else:
        print("uh you shouldnt get here like ever o no what is happen this is bad")
        return 0
    
'''
    getRotation - given the marker strings for the start and end markers, how many 90 degree rotations do we need?  
    String format example: "N3.5"
    N/E/S/W represents the wall the marker is on
    @param start - the start marker's string
    @param end - the end marker's string
    @return - the number of 90 degree turns necessary
        0 means no rotation, 2, means 180, 1 means clockwise, -1 means counterclockwise
''' 
def getRotation(start, end):
    swall = start[0]
    ewall = end[0]
    #just a lot of if-statements
    if(swall == ewall):            
        return 0
    if((swall == "N" and ewall == "S") or (swall == "S" and ewall == "N")):
        return 2
    elif((swall == "E" and ewall == "W") or (swall == "W" and ewall == "E")):
        return 2
    elif((swall == "N" and ewall == "E" ) or (swall == "S" and ewall == "W")):
        return 1
    elif((swall == "E" and ewall == "S") or (swall == "W" and ewall == "N")):
        return 1
    elif((swall == "N" and ewall == "W") or (swall == "S" and ewall == "E")):
        return -1
    elif((swall == "E" and ewall == "N") or (swall == "W" and ewall == "S")):
        return -1
    else:
        print("uh you shouldnt get here like ever o no what is happen this is bad")
        return 0
    
'''
    getDirectCoef - given the number of 90 degree rotations, what are the coefficients of the fly_direct?
    @param rotate - the number of 90 degree rotations
    @return - array where [1] is the pitch and [0] is the roll
'''
def getDirectCoef(rotate):
    coef = [0, 0]
    #a bunch of if statements dependent on rotate
    if rotate == 0:
        return coef
    elif rotate == 2:
        coef[1] = 10
        return coef
    else:
        coef[1] = 7
        coef[0] = 2*rotate
        return coef
              
'''
    search - find the enemy flag!
    strafes walls until it finds the flag, or receives info that the flag has been found
'''      
def search():
    '''
    psudocode for method:
        
    while flag not found:
		creep slowly clockwise slowly around the room
			(be tracking last seen marker)
		if last seen is a corner room, rotate 90 degrees
		if seen nothing for a while, move forward slightly
    transmit flag location
    done, probably
    '''
    global lastmarker
    global lastmidmarker
    global walldistance
    #until we know where their flag is

    while(enemyflag == -1):
        #creep slowly clockwise

                                                #of note here is vertical movement dependent on zdir
                                                #this makes the drone drift up and down as needed during the search
        mambo.fly_direct(roll=10, pitch=0, yaw=0, vertical_movement=zdir, duration=.2)
        #if we hit a corner, turn
            #checking both lastmarker and lastmidmarker to safeguard against bad marker reads
        if (lastmarker % 100 == 30 and (lastmidmarker == 11 or lastmidmarker == 12)) or (lastmarker % 100 == 49 and (lastmidmarker == 21 or lastmidmarker == 22)) or (lastmarker % 100 == 75 and (lastmidmarker == 34 or lastmidmarker == 33)) or (lastmarker % 100 >= 98 and (lastmidmarker == 44 or lastmidmarker == 45)):
            #sleeps here to make rotations safer
            mambo.smart_sleep(1)
            mambo.turn_degrees(90)
            mambo.smart_sleep(2)
            #change lastmarker so it doesnt 360 for 8 minutes
            lastmarker = lastmarker + 1
        #distance checking goes here
        #if too far, move forward a bit
        if (walldistance > 7):
            mambo.smart_sleep(1)
            mambo.fly_direct(roll=0, pitch=10, yaw=0, vertical_movement=0, duration=3)
            mambo.smart_sleep(1)
        #if too close, move backwards a bit
        if (walldistance < 4):
            mambo.smart_sleep(2)
            mambo.fly_direct(roll=0, pitch=-10, yaw=0, vertical_movement=0, duration=3)
            mambo.smart_sleep(1)
    
'''
    capture - capture the flag - go between their flag and our base repeatedly
    goes until game end
'''
def capture():
    '''
    pseudocode for method:
    
    if flag not scanned:
        go to flag location from current marker
            consists of rotate, fly until marker changes to another 4xx one, rotate back
        while flag not scanned, go in direction of flag from current marker
            if hit a corner or a couple markers over maybe:
                flip direction
    tag should be scanned by here
    go to base from current last known location
    while still holding flag, go in direction of base from current marker
        if hit a corner or a couple markers over maybe
            flip direction
    '''
    global lastmarker
    global enemyflag
    global zdir
    global basemarker

    #if we dont have the flag, head to their flag
    if not carryingflag:
        #find out how much we need to rotate
        rotate = getRotation(markerStrings[lastmarker%100], markerStrings[enemyflag%100])
        #save current location for later
        before = lastmarker
        #sleep before rotations for smoother rotations
        mambo.smart_sleep(1)
        mambo.turn_degrees(90*rotate)   #rotate the correct amount
        mambo.smart_sleep(2)
        lastmarker = -1
        #find the coefficients of the fly_direct
        coef = getDirectCoef(rotate)
        #until we find a new location, fly_direct based on coef's
        while lastmarker == -1:
            mambo.fly_direct(roll=coef[0], pitch=coef[1], yaw=0, vertical_movement=0, duration=.1)
        #stop upon arrival
        mambo.smart_sleep(1)
        
        #so now we made it to the wall, strafe along the wall in the general direction of where the flag probably is
        #until we find the flag...
        while not carryingflag:
            #move in the direction towards their flag
            direction = 1
            #large tolerances for the search
            if lastmarker%100 > enemyflag%100 + 1:
                direction = -1
            elif lastmarker%100 < enemyflag%100 - 2 and direction == -1:
                direction = 1
            #strafe again, using zdir as needed
            mambo.fly_direct(roll=7*direction, pitch=0, yaw=0, vertical_movement=zdir, duration=.1)
    
    #should have flag by here
    #find rotation necessary to get back to our base
    rotate = getRotation(markerStrings[lastmarker%100], markerStrings[basemarker])
    #save current location for same reasons
    before = lastmarker
    #sleep before rotations
    mambo.smart_sleep(1)
    mambo.turn_degrees(90*rotate)   #rotate the correct amount
    mambo.smart_sleep(2)
    lastmarker = -1
    #find the coefficients of the fly_direct
    coef = getDirectCoef(rotate)
    #until we find a new location, fly_direct based on coef's
    while lastmarker == -1:
        mambo.fly_direct(roll=coef[0], pitch=coef[1], yaw=0, vertical_movement=0, duration=.1)
    #stop upon arrival
    mambo.smart_sleep(1)
    
    #so now we made it to the wall, strafe along the wall in the general direction of where the base probably is
    #until we find the flag...
    while carryingflag:
        #move in the direction towards their flag
        direction = 1
        #large tolerances for the search
        if lastmarker%100 > basemarker%100 + 1:
            direction = -1
        elif lastmarker%100 < basemarker%100 - 2 and direction == -1:
            direction = 1
        #strafe again, using zdir as needed
        mambo.fly_direct(roll=7*direction, pitch=0, yaw=0, vertical_movement=0*zdir, duration=.1)

def demo_mambo_user_vision_function(mamboVision, args):
    """
    Demo the user code to run with the run button for a mambo

    :param args:
    :return:
    """
    #get the start time
    start = time.time()

    mambo = args[0]

    #check for testing variable
    if (testFlying):
        path = os.path.abspath('\FARTNoises\FartNoises.wav')
        os.system('start %s' % path).play()
        print("taking off!")
        mambo.safe_takeoff(5)

        #the core routine - search then capture forever
        search()
        while True:    
            capture()
            #if we hit the time limit (somehow)
            if time.time() - start > 250:
                break   #break from the loop and land

        print("landing")
        print("flying state is %s" % mambo.sensors.flying_state)
        mambo.safe_land(5)
    else:
        print("Sleeeping for 15 seconds - move the mambo around")
        mambo.smart_sleep(50)

    # done doing vision demo
    print("Ending the sleep and vision")
    mamboVision.close_video()

    mambo.smart_sleep(5)

    print("disconnecting")
    mambo.disconnect()


if __name__ == "__main__":
    # you will need to change this to the address of YOUR mambo
    mamboAddr = "e0:14:d0:63:3d:d0"

    #serial port needs to be global for use in callback function without having to set repeatedly
    global ser

    # make my mambo object
    # remember to set True/False for the wifi depending on if you are using the wifi or the BLE to connect
    mambo = Mambo(mamboAddr, use_wifi=True)
    print("trying to connect to mambo now")
    success = mambo.connect(num_retries=3)
    print("connected: %s" % success)

    #open port for serial communication with other team
    #timeout=0 means it doesn't wait to read in so doesn't hold up thread
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0)

    if (success):
        # get the state information
        print("sleeping")
        mambo.smart_sleep(1)
        mambo.ask_for_state_update()
        mambo.smart_sleep(1)

        print("Preparing to open vision")
        mamboVision = DroneVisionGUI(mambo, is_bebop=False, buffer_size=200,
                                     user_code_to_run=demo_mambo_user_vision_function, user_args=(mambo, ))
        userVision = UserVision(mamboVision)
        mamboVision.set_user_callback_function(userVision.marker_search, user_callback_args=None)
        mamboVision.open_video()
