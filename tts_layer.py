from gtts import gTTS
import pygame
import os
import time

def speak_to_user(text):
    print(f"[ET Concierge is saying]: {text}")
    
    # 1. Generate the speech using gTTS
    tts = gTTS(text=text, lang='en', slow=False)
    filename = "response.mp3"
    tts.save(filename)

    # 2. Initialize pygame mixer to play the audio
    pygame.mixer.init()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

    # 3. Wait for the audio to finish playing
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    
    # 4. Clean up: Stop the mixer and remove the file so it can be overwritten next time
    pygame.mixer.music.stop()
    pygame.mixer.quit()
    
    # Optional: remove file to keep directory clean
    try:
        os.remove(filename)
    except PermissionError:
        pass # Sometimes file is still locked by OS

# --- TEST IT ---
if __name__ == "__main__":
    speak_to_user("Hello Harsh! I am your Economic Times Concierge. How can I help you grow your wealth today?")