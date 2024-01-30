import mediapipe as mp
import time
import json
import numpy as np
from pynput.keyboard import Controller

keyboard = Controller()
# initialize mediapipe
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands

# This method will be injected into the class using Thread (it's already looping)
# !!!!method name can only be same as the file name!!!!
def Kick(self, image, config):
    if "Kick" not in config["KeySetting"]:
        config["KeySetting"]["Kick"] = {
            "Frequency": 50,
            "Sensitive": 50,
            "Keys": [
                {
                    "label": "Left Kick Key",
                    "key": "a"
                },
                {
                    "label": "Right Kick Key",
                    "key": "a"
                },
            ],
            "Checkboxes": []
        }
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
            
        self.update_config(config)
        # Save the config file
            
    # Initialize variables
    if not hasattr(self, "KickVars"):
        setattr(self, "KickVars", {
            "previous_left_leg_position": np.array([0, 0, 0]),
            "previous_right_leg_position": np.array([0, 0, 0]),
            "last_right_kick_time": 0,
            "last_left_kick_time": 0,
            "previous_frame_time" : 0,
            "threshold": config['KeySetting']['Kick']['Sensitive'] * 0.15,
            "interval": config['KeySetting']['Kick']['Frequency'] * 0.1,
        })
        
    if image is not None:
        with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
            # Process the image and detect poses
            results = pose.process(image)

            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            current_time = time.time()
            if results.pose_landmarks:
                elapsed_time = current_time - self.KickVars["previous_frame_time"]
                left_ankle = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_ANKLE]
                right_ankle = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ANKLE]

                # Check visibility of the wrists
                if left_ankle.visibility > self.visibility_threshold:
                    current_left_position = np.array([left_ankle.x, left_ankle.y, left_ankle.z])
                    if self.showedError:
                        self.errorSignal.emit("")
                        self.showedError = False
                else:
                    current_left_position = np.array([0, 0, 0])
                    if not self.showedError:
                        self.errorSignal.emit("Please make sure your whole leg is in the frame.")
                        self.showedError = True

                if right_ankle.visibility > self.visibility_threshold:
                    current_right_position = np.array([right_ankle.x, right_ankle.y, right_ankle.z])
                    if self.showedError:
                        self.errorSignal.emit("")
                        self.showedError = False
                else:
                    current_right_position = np.array([0, 0, 0])    
                    if not self.showedError:
                        self.errorSignal.emit("Please make sure your whole leg is in the frame.")
                        self.showedError = True

                left_speed = 0
                right_speed = 0

                # Calculate velocity vector for both hands
                left_velocity = current_left_position - self.KickVars["previous_left_leg_position"]
                left_speed = np.linalg.norm(left_velocity) / elapsed_time
                right_velocity = current_right_position - self.KickVars["previous_right_leg_position"]
                right_speed = np.linalg.norm(right_velocity) / elapsed_time

                # Left hand slashing detection
                if left_speed > self.KickVars["threshold"] and (current_time - self.KickVars['last_left_kick_time']) > self.KickVars["interval"]:
                    left_key_str = config["KeySetting"]["Kick"]["Keys"][0]["key"]
                    pynput_left_key = self.get_pynput_key(left_key_str)
                    
                    keyboard.press(pynput_left_key)
                    keyboard.release(pynput_left_key)
                    self.KickVars['last_left_kick_time'] = current_time

                # Right hand slashing detection
                if right_speed > self.KickVars["threshold"] and (current_time - self.KickVars['last_right_kick_time']) > self.KickVars["interval"]:
                    right_key_str = config["KeySetting"]["Kick"]["Keys"][1]["key"]
                    pynput_right_key = self.get_pynput_key(right_key_str)
                    
                    keyboard.press(pynput_right_key)
                    keyboard.release(pynput_right_key)
                    self.KickVars['last_right_kick_time'] = current_time

                self.KickVars["previous_left_leg_position"] = current_left_position
                self.KickVars["previous_right_leg_position"] = current_right_position
                self.KickVars["previous_frame_time"] = current_time
            return image