#!/usr/bin/env python
import rospy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy
from std_msgs.msg import String
import math

precise_cmd_in_operation = False

def joy_callback(msg):
    global precise_cmd_in_operation
    
    goal_command = Twist()
    distance = None
    angle = None

    if msg.buttons[3]==1:
        distance = -0.1
        angle = 0
        # mode = "forward"
        """ testing only """
        goal_command.linear.x = distance
        goal_command.angular.z = angle
        percise_cmd_pub.publish(goal_command)

        precise_cmd_in_operation = True
        while precise_cmd_in_operation:
            pass

        distance = 0
        angle = (math.pi / 2)
        # goal_command.linear.x = distance
        # goal_command.angular.z = angle
        # percise_cmd_pub.publish(goal_command)
        # while not precise_cmd_in_operation:
        #     pass



    elif msg.buttons[2]==1:
        distance = 0
        angle = (math.pi / 2)
        # mode = "turn_left"
    elif msg.buttons[0]==1:
        distance = 0
        angle = 0
        # mode = "stop"
    elif msg.buttons[1]==1:
        distance = 0
        angle = -(math.pi / 2)
        # mode = "forward"
    # else:
    #     distance = 0
    #     angle = 0

    # print(msg.buttons)

    if (distance!=None and angle!=None):
        goal_command.linear.x = distance
        goal_command.angular.z = angle
        percise_cmd_pub.publish(goal_command)

def precise_cmd_callback(precise_cmd_feedback_msg):
    global precise_cmd_in_operation

    precise_cmd_in_operation = False

if __name__ == '__main__':

    rospy.init_node('joy_send_command_node')
    joy_sub = rospy.Subscriber('joy', Joy, joy_callback)
    percise_cmd_pub = rospy.Publisher('control/precise_command',
                                       Twist, queue_size=1)
    precise_cmd_feedback_sub = rospy.Subscriber('control/precise_command/feedback',
                                       String, precise_cmd_callback)

    rate = rospy.Rate(100)
    while not rospy.is_shutdown():
        rate.sleep()
