# youtube_summary.py
import subprocess
import os
import webvtt
import requests
import json
import re
from dotenv import load_dotenv

# Cargar las variables de entorno
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
CHAT_API_URL = "https://api.openai.com/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

    
# Descargar transcripción de YouTube
def download_youtube_transcript(youtube_url):
    subprocess.run(["yt-dlp", "--write-auto-sub", "--sub-lang", "en", "--skip-download", youtube_url])
    files = os.listdir()
    vtt_files = [f for f in files if f.endswith(".vtt")]
    if vtt_files:
        return vtt_files[0]
    else:
        raise FileNotFoundError("No VTT files found. Please check the YouTube URL or subtitles availability.")

# Convertir VTT a texto plano
def vtt_to_text(vtt_file, txt_file):
    with open(txt_file, 'w', encoding='utf-8') as f:
        for caption in webvtt.read(vtt_file):
            f.write(caption.text + '\n')

# Limpiar la transcripción
def clean_transcript(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9.,?!\'" ]+', '', text)
    #return text.strip()
    cleaned_text = text.strip()

    # Guardar el texto limpio en un archivo
    with open('clean_transcript.txt', 'w', encoding='utf-8') as file:
        file.write(cleaned_text)

    return cleaned_text

# Ejemplo de cómo podrías usar esta función
# Supongamos que 'original_text' es el texto obtenido de alguna fuente
original_text = "Aquí va el texto original posiblemente con errores y duplicados."
clean_text = clean_transcript(original_text)
print("Texto limpio:", clean_text)

# Generar resumen con GPT-4
def summarize_text_via_request(text, model="gpt-4o"):
    '''
    messages = [
        {"role": "system", "content": "You are a helpful assistant specialized in summarizing sermons given in Christian churches."},
        {"role": "user", "content": ("You are an assistant specialized in summarizing sermons given in Christian churches. "
                                     "Your summaries should: "
                                     "1. Capture the core messages, including spiritual teachings, biblical references, y practical applications for everyday life. "
                                     "2. Identify the themes of the sermon (e.g., faith, love, repentance). "
                                     "3. Provide a summary in the following format:\n"
                                     "   - **Title**: [Title of the sermon]\n"
                                     "   - **Main Themes**: [Key themes identified]\n"
                                     "   - **Biblical References**: [Relevant biblical passages or verses]\n"
                                     "   - **Summary**: [Detailed summary capturing the core message]\n"
                                     "   - **Powerful Keywords**: A list of up to 10 keywords that capture the sermon’s essence.\n"
                                     "   - **Powerful Phrases**: Up to 5 powerful and inspiring frases que resuenen con los oyentes.\n"
                                     "\n"
                                     "Here is the sermon text:\n\n"
                                     f"{text}\n\n"
                                     "Provide the summary and keywords/phrases in this format:\n"
                                     "**Title**: [Title of the sermon]\n"
                                     "**Main Themes**: [List of main themes]\n"
                                     "**Biblical References**: [Relevant biblical passages or verses]\n"
                                     "**Summary**:\n"
                                     "**Powerful Keywords**:\n"
                                     "**Powerful Phrases**:")}
    ]
'''

    messages = [
        {"role": "system", "content": "You are a helpful assistant specialized in summarizing TED talks."},
        {"role": "user", "content": ("You are an assistant specialized in summarizing TED talks. "
                                     "Your summaries should: "
                                     "1. Capture the core messages, including key insights and important messages. "
                                     "2. Identify the themes of the talk (e.g., innovation, science, culture). "
                                     "3. Provide a summary in the following format:\n"
                                     "   - **Title**: [Title of the talk]\n"
                                     "   - **Main Themes**: [Key themes identified]\n"
                                     "   - **Key Points**: [Important points or messages]\n"
                                     "   - **Summary**: [Detailed summary capturing the core message]\n"
                                     "4. Generate a list of powerful keywords and phrases that will inspire and engage the audience, helping them remember the talk more clearly.\n"
                                     "   - **Powerful Keywords**: A list of up to 10 keywords that capture the talk’s essence.\n"
                                     "   - **Powerful Phrases**: Up to 5 powerful and inspiring phrases that resonate with the audience.\n"
                                     "\n"
                                     "Here is the talk text:\n\n"
                                     f"{text}\n\n"
                                     "Provide the summary and keywords/phrases in this format:\n"
                                     "**Title**: [Title of the talk]\n"
                                     "**Main Themes**: [List of main themes]\n"
                                     "**Key Points**: [Relevant points or messages]\n"
                                     "**Summary**:\n"
                                     "**Powerful Keywords**:\n"
                                     "**Powerful Phrases**:")}
    ]


    data = {
        "model": model,
        "messages": messages,
        "max_tokens": 1000,
        "temperature": 0.3,
        "n": 1
    }
    response = requests.post(CHAT_API_URL, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content'].strip()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return ""

# Función principal para descargar y resumir el video
def summarize_youtube_video(youtube_url):
    vtt_file = download_youtube_transcript(youtube_url)
    txt_file = 'transcript.txt'
    vtt_to_text(vtt_file, txt_file)

    if os.path.exists(txt_file):
        with open(txt_file, 'r', encoding='utf-8') as f:
            transcript = clean_transcript(f.read())

        final_summary = summarize_text_via_request(transcript)

        with open('summary.txt', 'w', encoding='utf-8') as f:
            f.write(final_summary)

        return final_summary
    else:
        raise FileNotFoundError(f"Error: Archivo {txt_file} no encontrado.")
