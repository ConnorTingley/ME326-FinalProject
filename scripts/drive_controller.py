#!/usr/bin/env python3

import time
import rospy
import tf
import numpy as np
import cv2

from occupancy_grid import OccupancyGrid
from path_planner import PathPlanner

class DriveController:
    def __init__(self):
        rospy.init_node('DriveController')
        self.mobile_base_vel_publisher = rospy.Publisher("/locobot/mobile_base/commands/velocity", Twist, queue_size=1)

        self.L = 0.025
        self.target = np.zeros(2)

        rospy.Subscriber("/locobot/mobile_base/odom", Odometry, self.OdometryCallback) #this says: listen to the odom message, of type odometry, and send that to the callback function specified

    def set_target(target):
        self.target = target

    def OdometryCallback(self, data):
        # Step 1: Calculate the point P location (distance L on the x-axis), and publish the marker so it can be seen in Rviz
        #first determine the relative angle of the mobile base in the world xy-plane, this angle is needed to determine where to put the point P
        #the rotation will be about the world/body z-axis, so we will only need the qw, and qz quaternion components. We can then use knoweldge of the 
        #relationship between quaternions and rotation matricies to see how we must rotate the Lx vector into the world (odom) frame and add it to the base position
        #to obtain the point P (for more info on quaterions, see a primer at the bottom of this page: https://arm.stanford.edu/resources/armlab-references)
        qw = data.pose.pose.orientation.w
        qx = data.pose.pose.orientation.x
        qy = data.pose.pose.orientation.y
        qz = data.pose.pose.orientation.z
        R11 = qw**2 + qx**2 - qy**2 -qz**2
        R12 = 2*qx*qz - 2*qw*qz
        R21 = 2*qx*qz + 2*qw*qz
        R22 = qw**2 - qx**2 + qy**2 -qz**2

        M = np.matrix([[R11,self.L*R12],[R21,self.L*R22]])


        px = data.pose.pose.position.x + self.L*R11
        py = data.pose.pose.position.y + self.L*R21
        p = np.array([px,py])

        k = 0.5
        u = np.ravel((k*np.linalg.inv(M)) @ (self.target - p).reshape((2,1)))

        v = u[0]
        w = u[1]
        control_msg = Twist()
        control_msg.linear.x = float(v) #forward velocity
        control_msg.angular.z = float(w) #angular velocity
        #now publish the control output:
        self.mobile_base_vel_publisher.publish(control_msg)
        # Now store these for plotting later:
        #control_msg_plot = TwistStamped()