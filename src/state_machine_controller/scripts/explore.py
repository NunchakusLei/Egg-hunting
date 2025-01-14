import rospy
import time
import math
import actionlib
from smach import State, StateMachine
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from std_msgs.msg import String
from sound_play.msg import SoundRequest
from sound_play.libsoundplay import SoundClient

# 45 degree turns smaller area:
# waypoints = [
    # [(-2.12, 2.88, 0.0), (0.0, 0.0, -0.93, 0.36)],

    # [(-2.45, -1.25, 0.0), (0.0, 0.0, -0.36, 0.93)],

    # # [(8.01, -2.03, 0.0), (0.0, 0.0, 0.36, 0.93)],
    # [(7.20, -1.44, 0.0), (0.0, 0.0, 0.35, 0.94)],

    # [(8.20, 2.26, 0.0), (0.0, 0.0, 0.92, 0.39)]
# ]

waypoints = [
    [(-2.12, 2.88, 0.0), (0.0, 0.0, -0.93, 0.36)],

    [(-2.45, -1.25, 0.0), (0.0, 0.0, -0.36, 0.93)],

    [(7.20, -1.44, 0.0), (0.0, 0.0, 0.35, 0.94)],

    [(6.92, 2.12, 0.0), (0.0, 0.0, 0.71, 0.71)]
]

# waypoints = [
    # [(-0.91, 2.27, 0.0), (0.0, 0.0, -0.95, 0.31)],

    # [(-2.45, -1.25, 0.0), (0.0, 0.0, -0.36, 0.93)],

    # [(7.20, -1.44, 0.0), (0.0, 0.0, 0.35, 0.94)],

    # [(7.16, 2.53, 0.0), (0.0, 0.0, 0.99, 0.01)]
# ]


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

def distance(position1, position2):
    dist_x = abs(position1.x - position2.x)
    dist_y = abs(position1.y - position2.y)
    return math.sqrt(dist_x**2 + dist_y**2)



class Explore(State):
    def __init__(self):
        State.__init__(self, outcomes=['success', 'lost'],
                input_keys=['docking_position'])
        self.side_detector = rospy.Subscriber('detector', String,
                self.side_detector_callback)
        self.client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
        self.client.wait_for_server()
        self.i = 0
        self.found = False
        self.arrived = False
        self.current_position = None
        self.last_docking_position = None
        self.rate = rospy.Rate(10)

        # self.ultrasonic = rospy.Subscriber('ultrasonic', String,
                # self.ultrasonic_cb)
        # self.ultrasonic_dist = None
        # self.ultrasonic_dock = None

    def execute(self, userdata):

        import os
        root = os.path.dirname(os.path.abspath(__file__))
        sound_src = root + '/super-mario-bros.wav'

        soundhandle = SoundClient()
        rospy.sleep(0.5)
        # sound_src = "/home/jimmy/Documents/CMPUT412/Egg-hunting/super-mario-bros.wav"
        soundhandle.playWave(sound_src)
        # rospy.sleep(1)

        self.found = False
        self.arrived = False
        while not rospy.is_shutdown():
            while self.i < len(waypoints):
                pose = waypoints[self.i]
                goal_position = goal_pose(pose)
                self.client.send_goal(goal_position,
                        feedback_cb = self.feedback_cb)

                # Wait for current_position
                while self.current_position == None:
                    self.rate.sleep()
                # Calculate the estimated distance and time to goal
                # assume moving speed is 0.4
                # dist_to_goal = distance(self.current_position, goal_position.target_pose.pose.position)
                # estmated_time = int(round(dist_to_goal / 0.4))

                # Set the timeout related to the estimated time to goal
                # timeout = getTimeSafe() + rospy.Duration(estmated_time+5)
                timeout = getTimeSafe() + rospy.Duration(25)

                while True:
                    if self.arrived:
                        self.arrived = False
                        self.found = False
                        self.client.cancel_goal()
                        self.i += 1
                        break
                    if self.found:
                        # Found target

                        # if self.last_docking_position == None or distance(
                                # self.current_position,
                                # self.last_docking_position
                                # ) > 0.8:

                        # Try if this is the first time entering this state
                        first_time = False
                        try:
                            dist_to_last = distance(
                                    userdata.docking_position,
                                    self.current_position)
                            print 'Distance to last target = ', dist_to_last
                        except KeyError:
                            first_time = True

                        # if (first_time or dist_to_last > 1.5) and self.ultrasonic_dock != None and self.ultrasonic_dock < 3000:
                        if first_time or dist_to_last > 0.75:
                            # Start docking
                            # self.last_docking_position = self.current_position
                            self.arrived = False
                            self.found = False
                            self.client.cancel_goal()
                            return 'success'

                    # Count timeout for re-localization
                    print 'time left:', timeout - getTimeSafe()
                    if getTimeSafe() > timeout:
                        self.client.cancel_goal()
                        return 'lost'

                    self.rate.sleep()

            self.i = 0



    def feedback_cb(self, feedback):
        current_position = feedback.base_position.pose.position
        self.current_position = current_position
        objective_position = goal_pose(waypoints[self.i]).target_pose.pose.position
        dist = distance(current_position, objective_position)
        # print 'distance to target = ', dist
        if dist < 0.5:
            self.arrived = True

    def side_detector_callback(self, msg):
        if msg.data == 'True':
            self.found = True
            # self.ultrasonic_dock = self.ultrasonic_dist

    # def ultrasonic_cb(self, msg):
        # self.ultrasonic_dist = int(msg.data)
