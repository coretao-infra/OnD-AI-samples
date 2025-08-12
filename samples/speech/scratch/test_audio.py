#!/usr/bin/env python3
"""
Simple audio device tester - minimal imports, maximum clarity
"""

import sounddevice as sd
import numpy as np
import sys

def list_devices():
    """List only real microphone devices"""
    print("=== MICROPHONE DEVICES ===")
    devices = sd.query_devices()
    mic_devices = []
    
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            name = device['name'].lower()
            # Filter for actual microphones (exclude system audio devices)
            if ('microphone' in name or 'mic' in name or 'headset' in name) and \
               'stereo mix' not in name and 'pc speaker' not in name and 'what u hear' not in name:
                marker = " <-- DEFAULT" if i == sd.default.device[0] else ""
                print(f"{i:2d}: {device['name']} (IN: {device['max_input_channels']}ch @ {device['default_samplerate']:.0f}Hz){marker}")
                mic_devices.append(i)
    
    if not mic_devices:
        print("❌ No microphone devices found!")
    return mic_devices

def test_device_loop(device_id):
    """Test recording from a device in a continuous loop with visual feedback"""
    print(f"\n=== TESTING DEVICE {device_id} (CONTINUOUS) ===")
    
    try:
        info = sd.query_devices(device_id)
        print(f"Device: {info['name']}")
        print(f"Channels: {info['max_input_channels']}")
        print(f"Default rate: {info['default_samplerate']}")
        
        if info['max_input_channels'] == 0:
            print("❌ No input channels - this is not an input device")
            return False
            
        print(f"\n🎙️ Listening... (Press Ctrl+C to stop)")
        print("Make noise near your microphone to test!")
        print("Legend: 🔇=silence  🔉=quiet  🔊=loud")
        
        rate = int(info['default_samplerate'])
        
        # Use callback-based approach to avoid blocking API issues
        audio_data = {'latest': np.zeros(1024), 'max_val': 0.0}
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Status: {status}")
            audio_data['latest'] = indata[:, 0].copy()
            audio_data['max_val'] = np.max(np.abs(indata[:, 0]))
        
        try:
            with sd.InputStream(
                samplerate=rate, 
                channels=1, 
                device=device_id,
                callback=audio_callback,
                blocksize=1024
            ):
                import time
                frame_count = 0
                print("🔊 Audio stream started!")
                
                while True:
                    time.sleep(0.1)  # Check every 100ms
                    max_val = audio_data['max_val']
                    
                    # Visual indicator based on amplitude
                    if max_val > 0.1:
                        indicator = "🔊"
                        level = "LOUD"
                    elif max_val > 0.01:
                        indicator = "🔉"  
                        level = "quiet"
                    else:
                        indicator = "🔇"
                        level = "silence"
                    
                    # Update display every 10 frames (~1 second)
                    frame_count += 1
                    if frame_count % 10 == 0:
                        print(f"\r{indicator} {level} (max: {max_val:.6f})     ", end="", flush=True)
                    
        except KeyboardInterrupt:
            print(f"\n✅ Test completed successfully!")
            return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def main():
    mic_devices = list_devices()
    
    if not mic_devices:
        print("\n❌ No microphone devices found!")
        return
    
    try:
        device_input = input(f"\nEnter device ID to test (available: {mic_devices}) or press Enter for first mic: ").strip()
        
        if not device_input:
            device_id = mic_devices[0]
            print(f"Using first microphone: {device_id}")
        else:
            device_id = int(device_input)
            
        if device_id not in mic_devices:
            print(f"⚠️  Device {device_id} is not in the microphone list, but trying anyway...")
            
        success = test_device_loop(device_id)
        
        if success:
            print("\n🎉 This microphone works! It should work in the main app too.")
        else:
            print("\n💥 This microphone doesn't work.")
            
    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()
