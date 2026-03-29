import speech_recognition as sr

def listen_to_user():
    recognizer = sr.Recognizer()
    
    # We are forcing Index 3 (Your Realtek Mic)
    # If Index 3 fails, change this to 10
    mic_index = 2 
    
    try:
        with sr.Microphone(device_index=mic_index) as source:
            print(f"\n[System] Using Mic Index {mic_index}. Calibrating...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            
            print("[ET Concierge] I'm listening... Speak now.")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            print("[System] Recognizing...")
            text = recognizer.recognize_google(audio)
            return text
            
    except Exception as e:
        print(f"[Hardware Error] {e}")
        return None

if __name__ == "__main__":
    result = listen_to_user()
    if result:
        print(f"STT Success: {result}")
    else:
        print("STT Failed. Try changing mic_index to 10.")