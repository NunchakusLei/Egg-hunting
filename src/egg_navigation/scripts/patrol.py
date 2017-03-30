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

waypoints = [
    [(-2.15, 2.58, 0.0), (0.0, 0.0, -0.71, 0.70)],
    [(-2.71, -1.21, 0.0), (0.0, 0.0, -0.00, 0.99)],
    [(7.99, -2.18, 0.0), (0.0, 0.0, 0.69, 0.72)],
    [(8.10, 2.21, 0.0), (0.0, 0.0, 0.99, 0.01)]
]


client = None
force_stop = False
current_goal = None
pause = False


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
    global client, to_main, force_stop
    # time.sleep(2)
    # client.cancel_goal()
    # force_stop = True

    if msg.data == 'True':
        client.cancel_goal()
        to_main.publish('Cacelled')
        while pause:
            time.sleep(0.1)
        client.send_goal(current_goal)

def main_cmd_callback(msg):
    global pause
    if msg.data == 'Start':
        pause = False


def pose_callback(msg):
    # print msg.pose
    pass


def main():
    global trig
    global force_stop
    global current_goal
    global client
    
    rospy.init_node('patrol')

    detector_sub = rospy.Subscriber('detector', String, detector_callback)
    pose_sub = rospy.Subscriber('amcl_pose', PoseWithCovarianceStamped, pose_callback)

    client = actionlib.SimpleActionClient('move_base', MoveBaseAction)  # <3>
    client.wait_for_server()

    rospy.wait_for_service('global_localization')
    global_localization = rospy.ServiceProxy('global_localization', Empty)
    global_localization() # reset pose to start amcl

    # Wander:
    # cmd_vel_pub = rospy.Publisher('cmd_vel_mux/input/teleop', Twist, queue_size=1)
    # move = Movement()
    # tw = Twist()
    # linear_range = np.linspace(2, 7, 10)
    # angular_range = np.linspace()

    
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
