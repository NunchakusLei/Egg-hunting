#!/usr/bin/env python

import rospy
import actionlib
import tf
import os
import time
import numpy as np

from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
# from sensor_msgs.msg import Joy
from std_msgs.msg import String
from std_srvs.srv import Empty
from geometry_msgs.msg import PoseWithCovarianceStamped

from geometry_msgs.msg import Twist
from ramp import Movement


# Counterclockwise safe:
# waypoints = [
    # [(6.29, -1.80, 0.0), (0.0, 0.0, 0.63, 0.78)],
    # [(6.31, 1.23, 0.0), (0.0, 0.0, 0.99, 0.09)],
    # [(0.63, 1.43, 0.0), (0.0, 0.0, -0.78, 0.62)],
    # [(0.49, -1.39, 0.0), (0.0, 0.0, -0.17, 0.98)]
# ]
waypoints = [
    # [(-2.43, 2.99, 0.0), (0.0, 0.0, -0.716, 0.70)],
    # [(-2.72, -1.91, 0.0), (0.0, 0.0, 0.14, 0.99)],
    # [(-0.01, -0.19, 0.0), (0.0, 0.0, 0.01, 0.99)],
    # [(5.07, -1.71, 0.0), (0.0, 0.0, -0.11, 0.99)],
    # [(8.10, -2.33, 0.0), (0.0, 0.0, 0.70, 0.71)],
    # [(8.42, 2.35, 0.0), (0.0, 0.0, 0.99, 0.02)]

    # [(-2.38, 2.94, 0.0), (0.0, 0.0, -0.72, 0.69)],
    # [(-2.64, -1.45, 0.0), (0.0, 0.0, -0.01, 0.99)],
    # [(7.99, -2.18, 0.0), (0.0, 0.0, 0.69, 0.72)],
    # [(8.36, 2.29, 0.0), (0.0, 0.0, 1.00, 0.02)]

    [(-2.15, 2.58, 0.0), (0.0, 0.0, -0.71, 0.70)],
    [(-2.71, -1.21, 0.0), (0.0, 0.0, -0.00, 0.99)],
    [(7.99, -2.18, 0.0), (0.0, 0.0, 0.69, 0.72)],
    [(8.10, 2.21, 0.0), (0.0, 0.0, 0.99, 0.01)]
]


client = None
trig = False
force_stop = False
current_goal = None


def goal_pose(pose):
    goal_pose = MoveBaseGoal()
    goal_pose.target_pose.header.frame_id = 'map'
    goal_pose.target_pose.pose.position.x = pose[0][0]
    goal_pose.target_pose.pose.position.y = pose[0][1]
    goal_pose.target_pose.pose.position.z = pose[0][2]
    goal_pose.target_pose.pose.orientation.x = pose[1][0]
    goal_pose.target_pose.pose.orientation.y = pose[1][1]
    goal_pose.target_pose.pose.orientation.z = pose[1][2]
    goal_pose.target_pose.pose.orientation.w = pose[1][3]
    return goal_pose


def joy_callback(msg):
    global trig
    global client
    if msg.buttons[2]==1:
        trig = not trig
        print 'trigger =', trig
    elif msg.buttons[1]==1:
        print 'Exit...'
        client.cancel_all_goals()
        force_stop = True
        # os._exit(0)


def detector_callback(msg):
    global client
    if msg.data == 'True':
        client.cancel_all_goals()
        raw_input('wait here')
        client.send_goal(current_goal)


def pose_callback(msg):
    # print msg.pose
    pass


def main():
    global trig
    global force_stop
    global current_goal
    global client
    
    rospy.init_node('patrol')
    # joy_sub = rospy.Subscriber('joy', Joy, joy_callback)


    detector_sub = rospy.Subscriber('detector', String, detector_callback)
    pose_sub = rospy.Subscriber('amcl_pose', PoseWithCovarianceStamped, pose_callback)
    client = actionlib.SimpleActionClient('move_base', MoveBaseAction)  # <3>
    # rospy.wait_for_service('global_localization')
    # global_localization = rospy.ServiceProxy('global_localization', Empty)

    client.wait_for_server()

    # print 'Press enter to start amcl localization'
    # raw_input()
    # print 'press start key to start amcl localization, after that you should move robot until it finds its location'
    # while not trig:
        # pass
    # global_localization() # reset pose to start amcl
    # global_localization(Empty()) # reset pose to start amcl
    # trig = False

    # Wander:
    # cmd_vel_pub = rospy.Publisher('cmd_vel_mux/input/teleop', Twist, queue_size=1)
    # move = Movement()
    # tw = Twist()
    # linear_range = np.linspace(2, 7, 10)
    # angular_range = np.linspace()



    # print 'press enter to start'
    # print 'press start key to go to the initial point'
    # raw_input()
    # while not trig:
        # pass
    # trig = False

    # Go to the start point:
    # client.send_goal(goal_pose(waypoints[0]))
    # client.wait_for_result()

    # print 'press start key to start navigation'
    # # raw_input()
    # while not trig:
        # pass
    
    while not rospy.is_shutdown():
        for pose in waypoints:
            print 'send goal pose', pose
            goal = goal_pose(pose)
            current_goal = goal
            client.send_goal(goal)
            client.wait_for_result()
            if force_stop:
                return


if __name__ == '__main__':
    main()
