

# import the necessary packages
from imutils.video import VideoStream
import argparse
import datetime
import imutils
import time
import cv2

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", default="videos/parking2.mp4", help="path to the video file")
ap.add_argument("-a", "--min-area", type=int, default=500, help="minimum area size")
args = vars(ap.parse_args())

# if the video argument is None, then we are reading from webcam
if args.get("video", None) is None:
	vs = VideoStream(src=0).start()
	time.sleep(2.0)

# otherwise, we are reading from a video file
else:
	vs = cv2.VideoCapture(args["video"])

# initialize the first frame in the video stream
firstFrame = None

parking_time = 10
pex = 0
cnt = 0
limit = 100
zone1 = (350,200)
zone2 = (480, 100)
vehic = []
pcar = {}
isCaptured = False

# loop over the frames of the video
while True:
	#print(cnt)
	# grab the current frame and initialize the occupied/unoccupied
	# text
	new_vehic = []
	frame = vs.read()
	frame = frame if args.get("video", None) is None else frame[1]
	text = ""

	# if the frame could not be grabbed, then we have reached the end
	# of the video
	if frame is None:
		break

	# resize the frame, convert it to grayscale, and blur it
	frame = imutils.resize(frame, width=500)
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, (21, 21), 0)

	# if the first frame is None, initialize it
	if firstFrame is None:
		firstFrame = gray
		continue

	# compute the absolute difference between the current frame and
	# first frame
	frameDelta = cv2.absdiff(firstFrame, gray)
	thresh = cv2.threshold(frameDelta, 35, 255, cv2.THRESH_BINARY)[1]

	# dilate the thresholded image to fill in holes, then find contours
	# on thresholded image
	thresh = cv2.dilate(thresh, None, iterations=2)
	cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)
	cnts = cnts[0] if imutils.is_cv2() else cnts[1]
	dis = None
	vehic_min = None
	dis_min = float('inf')
	isCar = False    
	flag = {}
	# loop over the contours
	for c in cnts:
		# if the contour is too small, ignore it
		if cv2.contourArea(c) < args["min_area"]:
			continue

		# compute the bounding box for the contour, draw it on the frame,
		# and update the text
		(x, y, w, h) = cv2.boundingRect(c)
		if ((x+w/2)>zone1[0]-100 and (x+w/2)<zone2[0]+100 and (y+h/2)<zone1[1]+100 and (y+h/2)>zone2[1]-100):
			isCar = True            
		xx = int(x)
		yy = int(y)
		new_vehic.append((xx,yy))	
		if 	(xx,yy) in vehic:
				if (xx,yy) in pcar:
						pcar[(xx,yy)] += 1
				else:
						pcar[(xx,yy)] = 1						
		else:
				pcar[(xx,yy)] = 0  

		if pcar[(xx,yy)] > 1:
				pex = 1
		#cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 0), 2)
		if pex==1 and (x+w/2)>zone1[0] and (x+w/2)<zone2[0] and (y+h/2)<zone1[1] and (y+h/2)>zone2[1]:
			#print("Hello")
			pex = 0            
			rcar = frame[y:y+h, x:x+w]
			rcar = cv2.resize(rcar, (0,0), fx=4, fy=4)
			time = pcar[(xx,yy)]/30
			col = (0, 255, 0)
			if time > parking_time:
				col = 	(0, 0, 255) 
				text = "<Illegal Parking>"                
				if isCaptured == False:
					cv2.imwrite('reported_parking/reported_car_'+str(cnt)+".jpg",rcar)
					cnt+=1
					isCaptured = True
                    
			else:
				isCaptured = False                
			cv2.putText(frame, 'time : '+str(int(time)) + ' sec', (350, 85),
		cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 2)            
		cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 0), 2)
	if isCar == False:
		firstFrame = gray
        
	vehic = new_vehic
		
	# draw the text and timestamp on the frame
	color = (0, 255, 0)
	
        
	cv2.rectangle(frame, zone1, zone2, (255, 0, 0), 2)
	#cv2.rectangle(firstFrame, zone1, zone2, (255, 0, 0), 2)    
	cv2.putText(frame, "{}".format(text), (10, 20),
		cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
	cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
		(10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)
	

	# show the frame and record if the user presses a key
	cv2.imshow("Security Feed", frame)
	cv2.imshow("Thresh", thresh)
	cv2.imshow("Frame Delta", frameDelta)
	cv2.imshow("Frist Frame", firstFrame)    
	key = cv2.waitKey(1) & 0xFF

	# if the `q` key is pressed, break from the lop
	if key == ord("q"):
		break

# cleanup the camera and close any open windows
#vs.stop() if args.get("video", None) is None else vs.release()
cv2.destroyAllWindows()