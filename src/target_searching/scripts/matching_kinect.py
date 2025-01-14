#!/usr/bin/python
import rospy, os
from sensor_msgs.msg import Image
from std_msgs.msg import Float32
import cv_bridge
import cv2
import numpy as np
from matplotlib import pyplot as plt
from scipy.misc import imresize
import scipy
import cPickle as pickle
import os

showVideo = False
showDepthVideo = False
decay = 0.5
root = os.path.dirname(os.path.abspath(__file__))

class LogoDetector:
    def __init__(self):
        self.rate = rospy.Rate(10)
        self.image_sub = rospy.Subscriber('camera/rgb/image_raw',
                Image, self.image_callback)
        self.depth_sub = rospy.Subscriber('camera/depth/image_raw',
                Image, self.depth_callback)
        self.x_pub = rospy.Publisher('detector_x', Float32, queue_size=1)

        self.bridge = cv_bridge.CvBridge()
        self.depth_bridge = cv_bridge.CvBridge()
        self.image = None
        self.depth = None

        # Prepare templates at multiple scales:
        root = os.path.dirname(os.path.abspath(__file__))
        self.template_original = cv2.imread(root+'/logo.png',0)
        self.template_original = imresize(self.template_original, 0.8)
        self.template_original = cv2.GaussianBlur(self.template_original, (9,9), 0)
        # self.template_original = cv2.blur(self.template_original, (9,9))
        # cv2.imshow('original template', self.template_original)
        self.last_x = None

        with open(root+'/param/kinect_logo.bin', 'rb') as f:
            self.kh, self.kw = pickle.load(f)

    def image_callback(self, msg):
        self.image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

    def depth_callback(self, msg):
        self.depth = self.depth_bridge.imgmsg_to_cv2(msg)

    def detection(self, frame, p0, p1):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # gray = cv2.GaussianBlur(gray, (9,9), 0)

        # methods = ['cv2.TM_CCOEFF_NORMED']
        # for meth in methods:
            # method = eval(meth)
        method = eval('cv2.TM_CCOEFF_NORMED')

        template = self.template_original

        # Calculate the mean distance from depth image:
        x0, y0 = p0
        x1, y1 = p1
        depth = self.depth.copy()
        region = depth[y0:y1, x0:x1]
        dist = np.nanmean(region.astype(np.float32))

        # if np.isnan(dist) or dist < 1.0:
            # self.x_pub.publish(-1.0)

        if not np.isnan(dist) and dist > 1.0:
            # print 'dist:', dist
            # w = int(round(94895.492 / dist))
            # h = int(round(119687.266 / dist))
            w = int(round(self.kw / dist))
            h = int(round(self.kh / dist))

            # test rectangle:
            if showVideo:
                tx0 = int(round(320-w/2))
                tx1 = int(round(320+w/2))
                ty0 = int(round(240-h/2))
                ty1 = int(round(240+h/2))
                tp0 = tx0, ty0
                tp1 = tx1, ty1
                cv2.rectangle(frame, tp0, tp1, (0,255,0), 2)

            if h < gray.shape[0] and w < gray.shape[1] and h > 30 and w > 30:
                template = imresize(template, (h, w))
                res = cv2.matchTemplate(gray, template, method)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                if max_val > 0.45:
                    pt = max_loc

                    # Calculate and smooth the x coordnate of the logo:
                    x = pt[0] + w/2
                    if self.last_x != None:
                        x = (1 - decay) * x + decay * self.last_x
                    self.x_pub.publish(x)
                    self.last_x = x

                    if showVideo:
                        cv2.rectangle(frame, pt, (pt[0]+w, pt[1]+h), (0,0,255), 2)
                else:
                    # not found
                    self.x_pub.publish(-1.0)
            else:
                # template size too big or too small
                self.x_pub.publish(-1.0)
        else:
            # wrong distance
            self.x_pub.publish(-1.0)

        if showVideo:
            cv2.imshow('front detector', frame)


            # template = imresize(template, (h, w))
            # res = cv2.matchTemplate(gray, template, method)
            # min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            # pt = max_loc
            # if max_val > 0.45:
                # cv2.rectangle(frame, pt, (pt[0]+w, pt[1]+h), (0,0,255), 2)
                # x = pt[0] + w/2
                # if self.last_x != None:
                    # x = (1 - decay) * x + decay * self.last_x
                # self.x_pub.publish(x)
                # self.last_x = x
            # else:
                # self.x_pub.publish(-1.0)

            # loc = np.where(res > 0.45)
            # for pt in zip(*loc[::-1]):
                # cv2.rectangle(frame, pt, (pt[0]+w, pt[1]+h), (0,0,255), 2)
            # cv2.imshow('detector', frame)


    def spin(self):
        while not rospy.is_shutdown():
            if self.image == None:
                continue
            if self.depth == None:
                continue

            p0 = (300, 220) # (x, y)
            p1 = (340, 240) # (x, y)

            # Show depth image:
            if showDepthVideo:
                depth = self.depth.copy()
                cv2.normalize(depth, depth, 0, 255, cv2.NORM_MINMAX)
                depth = depth.astype(np.uint8)
                depth = cv2.cvtColor(depth, cv2.COLOR_GRAY2BGR)
                grid_y = np.linspace(200, 280, 2)
                grid_x = np.linspace(0, 639, 3)
                cv2.rectangle(depth, p0, p1, (0,0,255), 4)
                cv2.imshow('front depth', depth)

            frame = self.image.copy()
            self.detection(frame, p0, p1)

            if showVideo:
                if cv2.waitKey(1) & 0xff == ord('q'):
                    break
            self.rate.sleep()

        cv2.destroyAllWindows()

if __name__ == '__main__':
    rospy.init_node('logo_detector_front')
    logo = LogoDetector()
    logo.spin()
