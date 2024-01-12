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
def PunchTemplate(self, image, config):
     # Check if the config file has the key setting for this mode
    if "PunchTemplate" not in config["KeySetting"]:
        config["KeySetting"]["PunchTemplate"] = {
            "Frequency": 50,
            "Sensitive": 50,
            "Keys": [
                {
                    "label": "Punch Key",
                    "key": "Space"
                },
            ],
            "Checkboxes": []
        }
        
        self.update_config(config)
        # Save the config file
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
            
    # Initialize variables
    if not hasattr(self, "PunchTemplateVars"):
        setattr(self, "PunchTemplateVars", {
            "punch_previous_left_position": np.array([0, 0, 0]),
            "punch_previous_right_position": np.array([0, 0, 0]),
            "last_left_punch_time": None,
            "last_right_punch_time": 0,
            "punch_prev_time" : 0,
            "punch_threshold": config['KeySetting']['PunchTemplate']['Sensitive'] * 0.01,
            "punch_interval": config['KeySetting']['PunchTemplate']['Frequency'] * 0.01,
        })
        
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        results = pose.process(image)

        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        if results.pose_landmarks:
            current_time = time.time()
            elapsed_time = current_time - self.PunchTemplateVars["punch_prev_time"]
            left_wrist = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST]
            right_wrist = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST]

            # Update positions and calculate velocity
            if left_wrist.visibility > self.visibility_threshold:                      
                current_left_position = np.array([left_wrist.x, left_wrist.y, left_wrist.z])
                if self.showedError:
                    self.errorSignal.emit("")
                    self.showedError = False
            else:
                current_left_position = np.array([0, 0, 0])
                if not self.showedError:
                    self.errorSignal.emit("Please make sure your whole body is in the frame.")
                    self.showedError = True
            if right_wrist.visibility > self.visibility_threshold:
                current_right_position = np.array([right_wrist.x, right_wrist.y, right_wrist.z])
                if self.showedError:
                    self.errorSignal.emit("")
                    self.showedError = False
            else:
                current_right_position = np.array([0, 0, 0])
                if not self.showedError:
                    self.errorSignal.emit("Please make sure your whole body is in the frame.")
                    self.showedError = True
                
            left_velocity = current_left_position - self.PunchTemplateVars["punch_previous_left_position"]
            right_velocity = current_right_position - self.PunchTemplateVars["punch_previous_right_position"]

            left_speed = np.linalg.norm(left_velocity) / elapsed_time
            right_speed = np.linalg.norm(right_velocity) / elapsed_time
            
            punch_key_str = config["KeySetting"]["Punch"]["Keys"][0]["key"]
            pynput_punch_key = self.get_pynput_key(punch_key_str)
            # Check for left punch motion
            if left_speed > self.PunchTemplateVars["punch_threshold"] and (current_time - self.PunchTemplateVars["last_left_punch_time"]) > self.PunchTemplateVars["punch_interval"]:
                keyboard.press(pynput_punch_key)
                keyboard.release(pynput_punch_key)
                self.PunchTemplateVars["last_left_punch_time"] = current_time

            # Check for right punch motion
            if right_speed > self.PunchTemplateVars["punch_threshold"] and (current_time - self.PunchTemplateVars["last_right_punch_time"]) > self.PunchTemplateVars["punch_interval"]:
                keyboard.press(pynput_punch_key)
                keyboard.release(pynput_punch_key)
                self.PunchTemplateVars["last_right_punch_time"] = current_time

            self.PunchTemplateVars["punch_previous_left_position"] = current_left_position
            self.PunchTemplateVars["punch_previous_right_position"] = current_right_position
            self.PunchTemplateVars["punch_prev_time"] = current_time
            
        return image
    