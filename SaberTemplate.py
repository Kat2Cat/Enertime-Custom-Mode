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
def SaberTemplate(self, image, config):
    if "SaberTemplate" not in config["KeySetting"]:
        config["KeySetting"]["SaberTemplate"] = {
            "Frequency": 50,
            "Sensitive": 50,
            "Keys": [
                {
                    "label": "Left Saber Key",
                    "key": "a"
                },
                {
                    "label": "Right Saber Key",
                    "key": "d"
                }
            ],
            "Checkboxes": []
        }
        
        self.update_config(config)
        # Save the config file
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
            
    # Initialize variables
    if not hasattr(self, "SaberTemplateVars"):
        setattr(self, "SaberTemplateVars", {
            "saber_previous_left_position": np.array([0, 0, 0]),
            "saber_previous_right_position": np.array([0, 0, 0]),
            "last_right_slash_time": None,
            "last_left_slash_time": 0,
            "saber_prev_time" : 0,
            "saber_threshold": config['KeySetting']['SaberTemplate']['Sensitive'] * 0.1,
            "saber_interval": config['KeySetting']['SaberTemplate']['Frequency'] * 0.1,
        })
        
    if image is not None:
        with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
            # Process the image and detect poses
            results = pose.process(image)

            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            current_time = time.time()
            # Extract left and right wrist landmarks
            if results.pose_landmarks:
                elapsed_time = current_time - self.SaberTemplateVars["saber_prev_time"]
                left_wrist = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST]
                right_wrist = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST]

                # Check visibility of the wrists
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

                left_speed = 0
                right_speed = 0

                # Calculate velocity vector for both hands
                left_velocity = current_left_position - self.SaberTemplateVars["saber_previous_left_position"]
                left_speed = np.linalg.norm(left_velocity) / elapsed_time
                right_velocity = current_right_position - self.SaberTemplateVars["saber_previous_right_position"]
                right_speed = np.linalg.norm(right_velocity) / elapsed_time

                # Left hand slashing detection
                if left_speed > self.SaberTemplateVars["saber_threshold"] and (current_time - self.SaberTemplateVars['last_left_slash_time']) > self.SaberTemplateVars["saber_interval"]:
                    left_key_str = config["KeySetting"]["Saber"]["Keys"][0]["key"]
                    pynput_left_key = self.get_pynput_key(left_key_str)
                    
                    keyboard.press(pynput_left_key)
                    keyboard.release(pynput_left_key)
                    self.SaberTemplateVars['last_left_slash_time'] = current_time

                # Right hand slashing detection
                if right_speed > self.SaberTemplateVars["saber_threshold"] and (current_time - self.SaberTemplateVars['last_right_slash_time']) > self.SaberTemplateVars["saber_interval"]:
                    right_key_str = config["KeySetting"]["Saber"]["Keys"][1]["key"]
                    pynput_right_key = self.get_pynput_key(right_key_str)
                    
                    keyboard.press(pynput_right_key)
                    keyboard.release(pynput_right_key)
                    self.SaberTemplateVars['last_right_slash_time'] = current_time

                self.SaberTemplateVars["saber_previous_left_position"] = current_left_position
                self.SaberTemplateVars["saber_previous_right_position"] = current_right_position
                self.SaberTemplateVars["saber_prev_time"] = current_time
            return image