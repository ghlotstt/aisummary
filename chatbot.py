import os
import requests
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener la clave API de OpenAI desde las variables de entorno
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

app = Flask(__name__)
socketio = SocketIO(app)

# Función para interactuar con OpenAI API
def ask_openai(question, context, model="gpt-4o"):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [
            #{"role": "system", "content": "You are a helpful assistant."},
            {"role": "system", "content": "You are a helpful assistant trained to provide insights and summarize discussions from transcribed text."},

            {"role": "user", "content": question},

            {"role": "assistant", "content": context}
        ]
    }
    response = requests.post(OPENAI_API_URL, headers=headers, json=data)
    response_json = response.json()
    return response_json['choices'][0]['message']['content']
