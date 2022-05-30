import rospy
from sensor_msgs.msg import Image
from std_msgs.msg import Float64MultiArray
from cv_bridge import CvBridge
import cv2
from models import Yolov4

class YoloNode(object):
    def __init__(self):
        self.image = None
        self.imageBridge = CvBridge()
        self.loop_rate = rospy.Rate(10)
        self.TARGET_OBJECT = 'sports ball'
        self.DESTINATION_OBJECT = 'backpack'
        self.model = Yolov4(weight_path='weights/yolov4.weights', class_name_path='class_names/coco_classes.txt')

        # Publishers
        self.pub = rospy.Publisher('ball_pos', Float64MultiArray, queue_size=5)

        # Subscribers
        rospy.Subscriber('cv_camera/image_raw', Image, self.callback)

        rospy.loginfo("Initialized target calculation ...")

    def callback(self, msg):
        # rospy.loginfo('Image received...')
        self.image = self.imageBridge.imgmsg_to_cv2(msg)

    def start(self):
        rospy.loginfo("Starting target calculation...")
        self.loop()

    def loop(self):
        while not rospy.is_shutdown():
            if self.image is not None:
                self.image = cv2.flip(self.image, -1)
                prediction = self.model.predict_img(self.image, plot_img=False, return_output=True)
                datframe = prediction[1]
                msg = [-1.0, -1.0, -1.0, -1.0]

                if not datframe.empty:
                    targets = datframe.loc[datframe['class_name'] == self.TARGET_OBJECT]
                    destinations = datframe.loc[datframe['class_name'] == self.DESTINATION_OBJECT]

                    if not targets.empty:
                        sorted_lowest = targets.sort_values('y1', ascending=True)

                        nearest_target = sorted_lowest.iloc[0]
                        x1 = nearest_target['x1']
                        w = nearest_target['w']
                        x_center = x1 + 0.5 * w

                        y2 = nearest_target['y2']
                        h = nearest_target['h']
                        y_center = y2 + 0.5 * h

                        msg[0] = x_center / self.image.shape[1]
                        msg[1] = y_center / self.image.shape[0]

                    if not destinations.empty:

                        # assuming only one destination is set so take the one with highest confidence
                        destination = destinations[0]
                        x1 = destination['x1']
                        w = destination['w']
                        x_center = x1 + 0.5 * w

                        y2 = destination['y2']
                        h = destination['h']
                        y_center = y2 + 0.5 * h

                        msg[2] = x_center / self.image.shape[1]
                        msg[3] = y_center / self.image.shape[0]
            
            self.pub.publish(msg)
            self.loop_rate.sleep()

if __name__ == '__main__':
    rospy.init_node('target_calculation')
    node = YoloNode()
    node.start()
