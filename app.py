# app.py
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import threading
from notes import transcribe_audio, save_full_transcript
from dotenv import load_dotenv
import os
from summary import summarize_text, save_summary_to_docx
from youtube_summary import summarize_youtube_video
from chatbot import ask_openai
#from ted_transcription import process_ted_video


# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Crear aplicación Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback_secret_key')  # Fallback en caso de que falte la clave
socketio = SocketIO(app)

# Variable para controlar la transcripción
is_transcribing = False

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('start_transcription')
def start_transcription():
    global is_transcribing
    is_transcribing = True

    def send_transcript(transcript):
        if is_transcribing:
            socketio.emit('transcript', {'data': transcript})

    transcription_thread = threading.Thread(target=transcribe_audio, args=(send_transcript,), daemon=True)
    transcription_thread.start()

@socketio.on('stop_transcription')
def stop_transcription():
    global is_transcribing
    is_transcribing = False
    emit('transcription_stopped', {'data': 'Transcription stopped.'})

#===== Save Transcription ============================

@socketio.on('save_transcription')
def save_transcription(filename='transcription.txt'):
    try:
        save_full_transcript(filename)
        emit('transcription_saved', {'data': f'Transcription saved to {filename}'})
    except Exception as e:
        emit('transcription_error', {'data': str(e)})

#========== Summary Function =============================

@app.route('/generate_summary', methods=['POST'])
def generate_summary():
    data = request.get_json()
    transcript_file = request.json.get('filename', 'transcription.txt')
    #summary_type = request.json.get('summary_type', 'sermon')
    summary_type = data.get('summary_type', 'sermon')
    try:
        with open(transcript_file, 'r') as f:
            full_text = f.read()
        summary = summarize_text(full_text, summary_type)
        save_summary_to_docx(summary, 'summary.docx')
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
'''
@app.route('/generate_summary', methods=['POST'])
def generate_summary():
    data = request.get_json()
    transcript_file = data.get('filename', 'transcription.txt')
    summary_type = data.get('summary_type', 'sermon')

    try:
        with open(transcript_file, 'r') as file:
            full_text = file.read()

        # Aquí asumimos que tienes una función que genera el resumen basado en el texto completo
        summary = generate_dynamic_summary(full_text, summary_type)

        save_summary_to_docx(summary)
        return jsonify({'summary': summary})

    except FileNotFoundError:
        return jsonify({'error': 'Transcript file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
'''


def generate_dynamic_summary(text, summary_type):
    # Ejemplo de cómo podrías llamar a una API o generar un resumen
    # Supongamos que esta función devuelve un diccionario con el resumen generado
    response = some_api_call_to_generate_summary(text, summary_type)
    return {
        'title': response['title'],
        'themes': response['themes'],
        'key_points': response['key_points'],
        'detailed_summary': response['summary'],
        'keywords': response['keywords'],
        'phrases': response['phrases']
    }




@app.route('/generate_youtube_summary', methods=['POST'])
def generate_youtube_summary():
    youtube_url = request.json.get('youtube_url')
    if not youtube_url:
        return jsonify({'error': 'YouTube URL is required'}), 400
    try:
        summary = summarize_youtube_video(youtube_url)
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

'''  
# Endpoint para recibir preguntas y devolver respuestas
@app.route('/ask', methods=['POST'])
def get_answer():
    data = request.get_json()
    question = data['question']
    context = data['context']  # Este contexto podría ser el resumen o cualquier información relevante
    answer = ask_openai(question, context)
    return jsonify({'answer': answer})
'''

@app.route('/ask', methods=['POST'])
def get_answer():
    data = request.get_json()
    question = data['question']
    #context_source = data['contextSource']  # Esta línea captura la fuente del contexto seleccionada.
    context_source = data.get('contextSource', 'real-time')  # Usa get con un valor por defecto
    # Determinar el archivo basado en la selección del usuario
    if context_source == 'real-time':
        #transcript_file = 'clean_transcript.txt'
        transcript_file = 'transcription.txt'
    else:
        #transcript_file = 'clean_transcript.txt'
        transcript_file = 'transcription.txt'

    try:
        # Leer las últimas N líneas del archivo seleccionado como contexto
        with open(transcript_file, encoding='utf-8') as file:
            lines = file.readlines()
            context = ' '.join(lines[-10:])  # Cambia el número según lo que mejor funcione
    except FileNotFoundError:
        context = "No transcript available."
        print(f"{transcript_file} not found.")

    answer = ask_openai(question, context)
    return jsonify({'answer': answer})

'''
@app.route('/generate_ted_summary', methods=['POST'])
def generate_ted_summary():
    data = request.get_json()
    ted_url = data['ted_url']
    # Aquí iría el código para procesar la URL de TED, similar a cómo manejas YouTube
    summary = process_ted_video(ted_url)  # Asegúrate de que esta función esté definida y funcione correctamente
    return jsonify({'summary': summary})
'''



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)