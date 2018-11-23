import cv2
import numpy as np
import Vehicle
import time

#cv2.namedWindow('image', cv2.WINDOW_NORMAL)
#cv2.resizeWindow('image', 64,64)
cnt_up = 0
cnt_down = 0
zone1 = (100,200)
zone2 = (450, 100)

cap = cv2.VideoCapture('videos/traffic.avi')

# Capture the properties of VideoCapture to console
for i in range(19):
    print(i, cap.get(i))

w = cap.get(3)
h = cap.get(4)
frameArea = h*w
areaTH = frameArea/200
print('Area Threshold', areaTH)

# Input/Output Lines
line_up = int(2*(h/5))
line_down = int(3*(h/5))

up_limit = int(1*(h/5))
down_limit = int(4*(h/5))

print ("Red line y:", str(line_down))
print ("Blue line y:", str(line_up))
line_down_color = (255,0,0)
line_up_color = (0,0,255)
pt1 = [0, line_down]
pt2 = [w, line_down]
pts_L1 = np.array([pt1,pt2], np.int32)
pts_L1 = pts_L1.reshape((-1,1,2))
pt3 = [0, line_up]
pt4 = [w, line_up]
pts_L2 = np.array([pt3,pt4], np.int32)
pts_L2 = pts_L2.reshape((-1,1,2))

pt5 = [0, up_limit]
pt6 = [w, up_limit]
pts_L3 = np.array([pt5,pt6], np.int32)
pts_L3 = pts_L3.reshape((-1,1,2))
pt7 = [0, down_limit]
pt8 = [w, down_limit]
pts_L4 = np.array([pt7,pt8], np.int32)
pts_L4 = pts_L4.reshape((-1,1,2))

#Create the background subtractor
fgbg = cv2.createBackgroundSubtractorMOG2()

kernelOp = np.ones((3,3), np.uint8)
kernelOp2 = np.ones((5,5), np.uint8)
kernelCl = np.ones((11,11), np.uint8)

#Variables
font = cv2.FONT_HERSHEY_SIMPLEX
vehicles = []
max_p_age = 5
pid = 1

while(cap.isOpened()):
    #read a frame
    ret, frame = cap.read()

    for i in vehicles:
        i.age_one()     # age every person on frame

    #################
    # PREPROCESSING #
    #################
    fgmask = fgbg.apply(frame)
    fgmask2 = fgbg.apply(frame)

    # Binary to remove shadow
    try:
        #cv2.imshow('Frame', frame)
        #cv2.imshow('Backgroud Subtraction', fgmask)
        ret, imBin = cv2.threshold(fgmask, 200, 255, cv2.THRESH_BINARY)
        ret, imBin2 = cv2.threshold(fgmask2, 200, 255, cv2.THRESH_BINARY)
        #Opening (erode->dilate) to remove noise
        mask = cv2.morphologyEx(imBin, cv2.MORPH_OPEN, kernelOp)
        mask2 = cv2.morphologyEx(imBin2, cv2.MORPH_OPEN, kernelOp)
        #Closing (dilate->erode) to join white region
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernelCl)
        mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernelCl)
        cv2.imshow('Image Threshold', cv2.resize(fgmask, (400, 300)))
        cv2.imshow('Image Threshold2', cv2.resize(fgmask2, (400, 300)))
        cv2.imshow('Masked Image', cv2.resize(mask, (400, 300)))
        cv2.imshow('Masked Image2', cv2.resize(mask2, (400, 300)))
    except:
        #If there is no more frames to show...
        print('EOF')
        print('UP:', cnt_up)
        print('DOWN:', cnt_down)
        break

    ##################
    ## FIND CONTOUR ##
    ##################
   # cv2.rectangle(frame, zone1, zone2, (255, 0, 0), 2)
    _, contours0, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    for cnt in contours0:
        cv2.drawContours(frame, cnt, -1, (0,255,0), 3, 8)
        area = cv2.contourArea(cnt)
        #print area," ",areaTH
        if area > areaTH and area < 20000:
            ################
            #   TRACKING   #
            ################
            M = cv2.moments(cnt)
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            x,y,w,h = cv2.boundingRect(cnt)

            # the object is near the one which already detect before
            new = True
            for i in vehicles:
                if abs(x-i.getX()) <= w and abs(y-i.getY()) <= h:
                    new = False
                    i.updateCoords(cx,cy)   # Update the coordinates in the object and reset age
                    if i.going_UP(line_down, line_up) == True:
                        cnt_up += 1
                        print("ID:", i.getId(), 'crossed going up at', time.strftime("%c"))
                        cv2.putText(frame,str(i.getId()), (x, y-2), cv2.FONT_HERSHEY_SIMPLEX, 5, 255)   
                    elif i.going_DOWN(line_down, line_up) == True:
                        roi = frame[y:y+h, x:x+w]
                        cv2.imshow('Region of Interest', roi)
                        print("Area equal to ::::", area)
                        cnt_down += 1
                        print("ID:", i.getId(), 'crossed going down at', time.strftime("%c"))
                        cv2.putText(frame,str(i.getId()), (x, y-2), cv2.FONT_HERSHEY_SIMPLEX, 5, 255)   
                    break
                if i.getState() == '1':
                    if i.getDir() == 'down' and i.getY() > down_limit:
                        i.setDone()
                    elif i.getDir() == 'up' and i.getY() < up_limit:
                        i.setDone()
                if i.timedOut():
                    # Remove from the list person
                    index = vehicles.index(i)
                    vehicles.pop(index)
                    del i
            if new == True:
                p = Vehicle.MyVehicle(pid,cx,cy, max_p_age)
                vehicles.append(p)
                pid += 1

            ##################
            ##   DRAWING    ##
            ##################

            cv2.circle(frame,(cx,cy),5, (0,0,255), -1)
            img = cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
            #cv2.drawContours(frame, cnt, -1, (0,255,0), 3)
            #cv2.imshow('Image', cv2.resize(img, (400, 300)))

    for i in vehicles:
        """
        if len(i.getTracks()) >= 2:
            pts = np.array(i.getTracks(), np.int32)
            pts = pts.reshape((-1,1,2))
            frame = cv2.polylines(frame, [pts], False, i.getRGB())
        if i.getId() == 9:
            print str(i.getX()), ',', str(i.getY())
        """
        cv2.putText(frame, str(i.getId()), (i.getX(),i.getY()),font,0.3,i.getRGB(),1,cv2.LINE_AA)

    ###############
    ##   IMAGE   ##
    ###############
    str_up = 'UP: ' + str(cnt_up)
    str_down = 'DOWN: ' + str(cnt_down)
    frame = cv2.polylines(frame, [pts_L1], False, line_down_color, thickness=2)
    frame = cv2.polylines(frame, [pts_L2], False, line_up_color, thickness=2)
    frame = cv2.polylines(frame, [pts_L3], False, (255,255,255), thickness=1)
    frame = cv2.polylines(frame, [pts_L4], False, (255,255,255), thickness=1)
    cv2.putText(frame, str_up, (10,40),font,2,(255,255,255),2,cv2.LINE_AA)
    cv2.putText(frame, str_up, (10,40),font,2,(0,0,255),1,cv2.LINE_AA)
    cv2.putText(frame, str_down, (10,90),font,2,(255,255,255),2,cv2.LINE_AA)
    cv2.putText(frame, str_down, (10,90),font,2,(255,0,0),1,cv2.LINE_AA)


    cv2.imshow('Frame', cv2.resize(frame, (400, 300)))
    time.sleep(0.04)
    #cv2.imshow('Backgroud Subtraction', fgmask)

    #Abort and exit with 'Q' or ESC
    k = cv2.waitKey(10) & 0xff
    if k == 27:
        break

cap.release()
cv2.destroyAllWindows()
