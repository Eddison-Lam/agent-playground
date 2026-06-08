import soundfile as sf
from kokoro import Kokoro
from transformers import pipeline
import pyaudio 
import queue
import os

def play_audio(filename):
    """Initializes pygame mixer and plays the audio file."""
    print(f"Playing audio: {filename}...")
    
    # Initialize the mixer module
    pygame.mixer.init()
    
    # Load the audio file
    pygame.mixer.music.load(filename)
    
    # Play the audio
    pygame.mixer.music.play()
    
    # Keep the script alive while the audio is playing
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
        
    # Clean up audio resources so the file isn't locked
    pygame.mixer.music.unload()
    pygame.mixer.quit()
    print("Playback finished.")



def tts_and_play(text, output_filename="output.wav", voice_preset="af_bella"):

    print("Initializing Kokoro TTS model...")
    pipeline = Kokoro("hexgrad/Kokoro-82M", default_voice=voice_preset)
    
    print(f"Synthesizing audio using voice: '{voice_preset}'...")
    generator = pipeline(text, voice=voice_preset, speed=1.0, split_pattern=r'\n+')
    
    # Generate and save the audio file
    for _, _, audio in generator:
        sf.write(output_filename, audio, 24000)
        print(f"Audio saved to {output_filename}")
        break  # Process the first text block
        
    # Play the generated file
    if os.path.exists(output_filename):
        play_audio(output_filename)
    else:
        print("Error: Audio file was not generated.")

def tts_worker(text_pipeline):
    text_queue = text_pipeline
    audio_queue = queue.Queue()
    while True:
            text_chunk = text_queue.get()
            if text_chunk is None:  # Exit signal
                break
                
            # pipeline yields: (graphemes, phonemes, audio_numpy_array)
            generator = pipeline(text_chunk, voice=VOICE_PRESET, speed=1.0)
            
            for _, _, audio in generator:
                if audio is not None:
                    # Convert the float32 array (-1.0 to 1.0) into 16-bit PCM bytes
                    audio_int16 = (audio * 32767).astype(np.int16)
                    audio_bytes = audio_int16.tobytes()
                    audio_queue.put(audio_bytes)
                    
            text_queue.task_done()
            
        # Signal that the TTS engine is done producing audio
        audio_queue.put(None)        

def audio_player_worker():
    stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=SAMPLE_RATE,
            output=True
    )
        
    while True:
        audio_chunk = audio_queue.get()
        if audio_chunk is None:  # Exit signal
            break
            
        # Play the chunk to the speakers (blocks only for the duration of the clip)
        stream.write(audio_chunk)
        audio_queue.task_done()
        
    # Gracefully shut down hardware streams
    stream.stop_stream()
    stream.close()