import mediapipe as mp
import time
import json
import cv2 
from pynput.keyboard import Controller

keyboard = Controller()
# initialize mediapipe
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands

# This method will be injected into the class using Thread (it's already looping)
# !!!!method name can only be same as the file name!!!!    
def RotateTemplate(self, image, config):
    if "RotateTemplate" not in config["KeySetting"]:
        config["KeySetting"]["RotateTemplate"] = {
            "Frequency": 50,
            "Sensitive": 50,
            "Keys": [
                {
                    "label": "Left Rotate Key",
                    "key": "a"
                },
                {
                    "label": "Right Rotate Key",
                    "key": "d"
                }
            ],
            "Checkboxes": [
                {
                    "label": "Rotate Hold Key",
                    "checked": True
                }
            ]
        }
        
        self.update_config(config)
        # Save the config file
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
            
    # Initialize variables
    if not hasattr(self, "RotateTemplateVars"):
        setattr(self, "RotateTemplateVars", {
            "rotate_holding_left_key": False,
            "rotate_holding_right_key": False,
            "rotate_threshold": config['KeySetting']['RotateTemplate']['Sensitive'] * 0.01,
            "rotate_frequency": config['KeySetting']['RotateTemplate']['Frequency'] * 0.1,
            "RotateAllowLongPress": config["KeySetting"]["RotateTemplate"]["Checkboxes"][0]["checked"]
        })
        
    if image is not None:
        with mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5) as hands:
            # Process the image with MediaPipe
            image = cv2.flip(image, 1)
            results = hands.process(image)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw hand landmarks
                    mp_drawing.draw_landmarks(
                        image,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2),
                        mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2))

                # Calculate the line coordinates between the two hands
                if len(results.multi_hand_landmarks) == 2:
                    first_hand_landmarks = results.multi_hand_landmarks[0].landmark[mp_hands.HandLandmark.WRIST]
                    second_hand_landmarks = results.multi_hand_landmarks[1].landmark[mp_hands.HandLandmark.WRIST]
                        
                    x1, y1 = int(first_hand_landmarks.x * image.shape[1]), int(first_hand_landmarks.y * image.shape[0])
                    x2, y2 = int(second_hand_landmarks.x * image.shape[1]), int(second_hand_landmarks.y * image.shape[0])

                    if x2 - x1 == 0:    
                        slope = 0
                    else:
                        slope = (y2 - y1) / (x2 - x1)
                        
                    right_key_str = config["KeySetting"]["Rotate"]["Keys"][1]["key"]
                    pynput_right_key = self.get_pynput_key(right_key_str)
                    
                    left_key_str = config["KeySetting"]["Rotate"]["Keys"][0]["key"]
                    pynput_left_key = self.get_pynput_key(left_key_str)
                    if self.RotateAllowLongPress:
                        if slope > self.RotateTemplateVars["rotate_threshold"] and not self.RotateTemplateVars["rotate_holding_right_key"]:
                            keyboard.press(pynput_right_key)
                            self.RotateTemplateVars["rotate_holding_right_key"] = True
                            self.RotateTemplateVars["rotate_holding_left_key"] = False
                        elif slope < -self.RotateTemplateVars["rotate_threshold"] and not self.RotateTemplateVars["rotate_holding_left_key"]:
                            keyboard.press(pynput_left_key)
                            self.RotateTemplateVars["rotate_holding_left_key"] = True
                            self.RotateTemplateVars["rotate_holding_right_key"] = False
                        elif (self.RotateTemplateVars["rotate_holding_right_key"] or self.RotateTemplateVars["rotate_holding_left_key"])and (slope > -self.RotateTemplateVars["rotate_threshold"] and slope < self.RotateTemplateVars["rotate_threshold"]):
                            keyboard.release(pynput_left_key)
                            keyboard.release(pynput_right_key)
                            self.RotateTemplateVars["rotate_holding_right_key"] = False
                            self.RotateTemplateVars["rotate_holding_left_key"] = False
                    else:
                        sleep_time = 0.01 * (11 - self.RotateTemplateVars["rotate_frequency"])
                        if slope > self.RotateTemplateVars["rotate_threshold"]:
                            keyboard.press(pynput_right_key)
                            time.sleep(sleep_time)
                            keyboard.release(pynput_right_key)
                        elif slope < -self.RotateTemplateVars["rotate_threshold"]:
                            keyboard.press(pynput_left_key)
                            time.sleep(sleep_time)
                            keyboard.release(pynput_left_key)

            return image