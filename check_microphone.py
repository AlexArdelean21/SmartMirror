#!/usr/bin/env python3
"""
Simple microphone diagnostic tool
"""

import pyaudio
import numpy as np
import time

def check_microphone():
    """Check if microphone is working and show audio levels"""
    print("Microphone Diagnostic Tool")
    print("=" * 30)
    
    p = pyaudio.PyAudio()
    
    # List available audio devices
    print("\nAvailable Audio Devices:")
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if device_info['maxInputChannels'] > 0:
            print(f"  {i}: {device_info['name']} (Channels: {device_info['maxInputChannels']})")
    
    # Test default microphone
    print("\nTesting default microphone...")
    print("Speak into your microphone for 10 seconds...")
    
    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )
        
        max_level = 0
        start_time = time.time()
        
        while time.time() - start_time < 10:
            data = stream.read(1024, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            level = np.abs(audio_data).mean()
            max_level = max(max_level, level)
            
            # Show real-time level
            bar_length = int(level / 1000)
            bar = "█" * min(bar_length, 50)
            print(f"\rAudio Level: {level:6.0f} |{bar:<50}|", end="", flush=True)
            
            time.sleep(0.1)
        
        stream.stop_stream()
        stream.close()
        
        print(f"\n\nResults:")
        print(f"Maximum audio level detected: {max_level:.0f}")
        
        if max_level < 100:
            print("❌ Very low audio levels - check if microphone is muted or too far away")
        elif max_level < 500:
            print("⚠️  Low audio levels - try speaking louder or moving closer")
        elif max_level < 2000:
            print("✅ Good audio levels - microphone is working well")
        else:
            print("⚠️  Very high audio levels - might be too loud or too close")
            
    except Exception as e:
        print(f"\n❌ Error testing microphone: {e}")
    
    finally:
        p.terminate()

if __name__ == "__main__":
    check_microphone() 