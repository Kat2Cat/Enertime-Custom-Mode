import mediapipe as mp
import time
import json
from pynput.keyboard import Controller

keyboard = Controller()
# initialize mediapipe
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands

# This method will be injected into the class using Thread (it's already looping)
# !!!!method name can only be same as the file name!!!!
def JumpTemplate(self, image, config):
    # Check if the config file has the key setting for this mode
    if "JumpTemplate" not in config["KeySetting"]:
        config["KeySetting"]["JumpTemplate"] = {
            "Frequency": 50,
            "Sensitive": 50,
            "Keys": [
                {
                    "label": "Jump Key",
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
    if not hasattr(self, "JumpTemplateVars"):
        setattr(self, "JumpTemplateVars", {
            "jump_prev_left_hip": None,
            "jump_prev_right_hip": None,
            "jump_prev_time": None,
            "prev_jump_time": 0,
            "jump_threshold": config['KeySetting']['JumpTemplate']['Sensitive'] * 0.03,
            "jump_interval": config['KeySetting']['JumpTemplate']['Frequency'] * 0.01,
        })
        
    # Main function of the mode
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        # Make detection
        results = pose.process(image)
        # Extract landmarks
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            
            # Get coordinates
            left_hip = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y
            right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y

            if (landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].visibility < self.visibility_threshold or landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].visibility < self.visibility_threshold) and not self.showedError:
                self.errorSignal.emit("Please make sure your whole body is in the frame.")
                self.showedError = True
            elif (landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].visibility >= self.visibility_threshold or landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].visibility >= self.visibility_threshold) and self.showedError:
                self.errorSignal.emit("")
                self.showedError = False

            # Calculate the time difference between frames
            current_time = time.time()
            if self.JumpTemplateVars["jump_prev_time"] is not None:
                time_diff = current_time - self.JumpTemplateVars["jump_prev_time"]
            else:
                time_diff = 0.0

            # Calculate the upward speed of the hip landmarks
            left_hip_speed = self.calculate_speed(left_hip, self.JumpTemplateVars["jump_prev_left_hip"], time_diff)
            right_hip_speed = self.calculate_speed(right_hip, self.JumpTemplateVars["jump_prev_right_hip"], time_diff)
            # Check if the upward speed exceeds the threshold
            if (left_hip_speed > self.JumpTemplateVars["jump_threshold"] or right_hip_speed > self.JumpTemplateVars["jump_threshold"]) and (current_time - self.JumpTemplateVars["prev_jump_time"]) > self.JumpTemplateVars["jump_interval"]:
                jump_key_str = config["KeySetting"]["Jump"]["Keys"][0]["key"]
                pynput_jump_key = self.get_pynput_key(jump_key_str)
                keyboard.press(pynput_jump_key)
                keyboard.release(pynput_jump_key)
                self.JumpTemplateVars["prev_jump_time"] = current_time
            # Update the previous hip positions and timestamp
            self.JumpTemplateVars["jump_prev_left_hip"] = left_hip
            self.JumpTemplateVars["jump_prev_right_hip"] = right_hip
            self.JumpTemplateVars["jump_prev_time"] = current_time
            
        return image