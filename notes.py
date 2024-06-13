import pyaudio
from google.cloud import speech
from google.api_core import exceptions
from dotenv import load_dotenv
import os
import time
import grpc


# Cargar las variables de entorno desde el archivo .env
load_dotenv()


# Configurar las credenciales de Google Speech-to-Text
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")


# Configura el cliente de Google Speech-to-Text
client = speech.SpeechClient()
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=16000,
    language_code="en-US",
    max_alternatives=1,
)

streaming_config = speech.StreamingRecognitionConfig(
    config=config,
    interim_results=True  # True para recibir resultados provisionales
)

class MicrophoneStream:
    def __init__(self, rate, chunk):
        self.rate = rate
        self.chunk = chunk
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.buffer = []

    def __enter__(self):
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk,
            stream_callback=self.callback
        )
        return self

    def callback(self, in_data, frame_count, time_info, status):
        self.buffer.append(in_data)
        return (None, pyaudio.paContinue)

    def generator(self):
        while True:
            if self.buffer:
                data = self.buffer.pop(0)
                yield speech.StreamingRecognizeRequest(audio_content=data)

    def start(self):
        self.stream.start_stream()

    def stop(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


last_transcript = ""

# Global variable to store the entire transcript
full_transcript = []




def transcribe_audio(callback, max_duration=300):
    """Transcribe el audio en tiempo real y llama al callback con el texto transcrito.
    Reinicia automáticamente la transcripción para evitar exceder la duración máxima.
    """
    def recognize_stream():
        nonlocal last_transcript
        with MicrophoneStream(rate=16000, chunk=2048) as mic_stream:
            mic_stream.start()
            audio_generator = mic_stream.generator()
            requests = (request for request in audio_generator)
            responses = client.streaming_recognize(streaming_config, requests)

            for response in responses:
                for result in response.results:
                    if not result.is_final:
                        continue  # Ignora resultados no finales si solo se desean finales
                    transcript = result.alternatives[0].transcript

                    if transcript != last_transcript:
                        full_transcript.append(transcript)
                        callback(transcript)
                        last_transcript = transcript

    last_transcript = ""
    start_time = time.time()

    while True:
        try:
            recognize_stream()
        except (exceptions.OutOfRange, grpc.RpcError):
            print("Reiniciando transcripción debido a la duración máxima alcanzada...")
        elapsed_time = time.time() - start_time
        if elapsed_time >= max_duration:
            start_time = time.time()

def save_full_transcript(filename='transcription.txt'):
    """Guardar el transcript completo a un archivo."""
    with open(filename, 'w') as f:
        f.write("\n".join(full_transcript))