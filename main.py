#!/usr/bin/env python3


import cv2, os, sys, time
from threading import Thread, Semaphore


frameQueue = []
grayScaleQueue = []
# semaphores for consumer producer behaviour
# it blocks, waiting until some other thread calls release()
extract = Semaphore()
convert = Semaphore()
display = Semaphore()
#bound the limit of the queue
queueLimit = 10

class ExtractFrames(Thread):
    def __init__(self):
        Thread.__init__(self)
        # set variables used by this thread
        self.video = cv2.VideoCapture('clip.mp4')
        self.maxFrames = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.count = 0

    def run(self):
        success, image = self.video.read()

        while success and self.count <= 72:
            # check for queue limit so that we dont have more than 10 elements in the queue
            if len(frameQueue) <= queueLimit:
                # get extract permit 
                extract.acquire()
                frameQueue.append(image)

                success, image = self.video.read()
                print(f'Reading frame {self.count}')
                self.count += 1
                # realese convert permit, so that convert thread can use the permit to convert a frame
                convert.release()

        print('Frame extraction complete')

class ConvertToGrayScale(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.count = 0

    def run(self):
        while self.count <= 72:
            if frameQueue and len(grayScaleQueue) <= queueLimit:
                
                # aquire convert permit
                convert.acquire()
                # get frame to convert from the queue
                frame = frameQueue.pop(0)

                print(f'Converting frame {self.count}')
                grayFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                grayScaleQueue.append(grayFrame)
                self.count += 1
                
                # realese display permit to be used by display thread
                display.release()

        print('Finished converting to gray scale')          

class DisplayFrames(Thread):
    def __init__(self):
        Thread.__init__(self)
        # 42 ms display
        self.delay = 42
        self.count = 0

    def run(self):
        while self.count <= 72:
            # if queue is not empty
            if grayScaleQueue:
                # acquiere display permit display doesnt happen until is realeased by another thread
                display.acquire()
                # get black and gray frame
                frame = grayScaleQueue.pop(0)

                print(f'Displaying Frame {self.count}')
                # show the frame
                cv2.imshow('Video', frame)
                self.count += 1
                # realease extract semaphore to be available by another thread
                extract.release()

                if cv2.waitKey(self.delay) and 0xFF == ord('q'):
                    break
        
        print('Finished displaying all frames')
        cv2.destroyAllWindows()


# start threads to run concurrently

extractFrames = ExtractFrames()
extractFrames.start()

convertToGrayScale = ConvertToGrayScale()
convertToGrayScale.start()

displayFrames = DisplayFrames()
displayFrames.start()
