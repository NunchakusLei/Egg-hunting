import rospy
import time
import math
import actionlib
from smach import State, StateMachine
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from std_msgs.msg import String

# 45 degree turns smaller area:
waypoints = [
    [(-2.12, 2.88, 0.0), (0.0, 0.0, -0.93, 0.36)],
    [(-2.45, -1.25, 0.0), (0.0, 0.0, -0.36, 0.93)],
    [(8.01, -2.03, 0.0), (0.0, 0.0, 0.36, 0.93)],
    [(8.20, 2.26, 0.0), (0.0, 0.0, 0.92, 0.39)]
]

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

def getTimeSafe():
    while True:
        # rospy may returns zero, so we loop until get a non-zero value.
        time = rospy.Time.now()
        if time != rospy.Time(0):
            return time


class Explore(State):
    def __init__(self):
        State.__init__(self, outcomes=['success', 'lost'])
        self.side_detector = rospy.Subscriber('detector', String,
                self.side_detector_callback)
        self.client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
        self.client.wait_for_server()
        self.i = 0
        self.found = False
        self.arrived = False
        self.rate = rospy.Rate(10)

    def execute(self, userdata):
        self.found = False
        self.arrived = False
        while not rospy.is_shutdown():
            while self.i < len(waypoints):
                pose = waypoints[self.i]
                self.client.send_goal(goal_pose(pose),
                        feedback_cb = self.feedback_cb)


                timeout = getTimeSafe() + rospy.Duration(25)
                while True:
                    if self.arrived:
                        self.arrived = False
                        self.found = False
                        self.client.cancel_goal()
                        self.i += 1
                        break
                    if self.found:
                        self.arrived = False
                        self.found = False
                        self.client.cancel_goal()
                        return 'success'

                    print 'time left:', timeout - getTimeSafe()
                    if getTimeSafe() > timeout:
                        self.client.cancel_goal()
                        return 'lost'

                    self.rate.sleep()

            self.i = 0



    def feedback_cb(self, feedback):
        current_pose = waypoints[self.i]
        dist_x = abs(feedback.base_position.pose.position.x - current_pose[0][0])
        dist_y = abs(feedback.base_position.pose.position.y - current_pose[0][1])
        dist = math.sqrt(dist_x**2 + dist_y**2)
        # print 'distance to target = ', dist
        if dist < 0.5:
            self.arrived = True

    def side_detector_callback(self, msg):
        if msg.data == 'True':
            self.found = True
