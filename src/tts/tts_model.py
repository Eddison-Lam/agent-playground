import soundfile as sf
from kokoro import Kokoro
from transformers import pipeline


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