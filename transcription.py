from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

def transcribe_audio(audio_path, client):
    """
    Transcribe a single audio file and save the transcription to a text file.
    Returns the path of the saved transcription file.
    """
    try:
        audio_file = open(audio_path, "rb")
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        
        # Generate output path by replacing the audio extension with .txt
        output_path = audio_path.rsplit('.', 1)[0] + '.txt'
        
        # Save the transcription
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(transcript.text)
            
        print(f"Transcription saved to: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error processing {audio_path}: {str(e)}")
        return None
    finally:
        audio_file.close()

def process_recordings(directory):
    """
    Process all audio files in the specified directory.
    Supported formats: m4a, mp3, mp4, wav, webm
    """
    # Get API key from environment variable
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Supported audio formats
    audio_extensions = ('.m4a', '.mp3', '.mp4', '.wav', '.webm')
    
    # Process each audio file in the directory
    for filename in os.listdir(directory):
        if filename.lower().endswith(audio_extensions):
            audio_path = os.path.join(directory, filename)
            print(f"\nProcessing: {filename}")
            transcribe_audio(audio_path, client)

if __name__ == "__main__":
    # Directory containing the audio files
    recordings_dir = "C:/Users/Mark Wu/Desktop/aihackathon"
    process_recordings(recordings_dir)