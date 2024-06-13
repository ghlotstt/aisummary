
'''
import requests
from bs4 import BeautifulSoup
import re
import os
from dotenv import load_dotenv

# Carga las variables de entorno
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
CHAT_API_URL = "https://api.openai.com/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def download_ted_transcript(ted_url):
    response = requests.get(ted_url)
    if response.status_code != 200:
        raise Exception("Failed to fetch TED page, status code:", response.status_code)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    
    # Busca el contenedor de la transcripción (ajusta según la estructura de TED)
    transcript_tag = soup.find('div', {'data-cy': 'transcript'})
    if transcript_tag:
        return transcript_tag.get_text(separator='\n')
    else:
        raise FileNotFoundError("No transcript found. Please check the TED URL.")

def ted_clean_transcript(text):
    # Normaliza los espacios y elimina caracteres no deseados
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9.,?!\'" ]+', '', text)
    return text.strip()

def ted_summarize_text(text, model="gpt-4-turbo"):
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
        "temperature": 0.5,
        "n": 1
    }
    response = requests.post(CHAT_API_URL, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content'].strip()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return ""

def process_ted_video(ted_url):
    # Descargar la transcripción desde TED
    transcript = download_ted_transcript(ted_url)
    
    # Limpieza de la transcripción
    cleaned_text = ted_clean_transcript(transcript)
    
    # Guardar la transcripción limpia en un archivo
    with open('ted_transcript.txt', 'w', encoding='utf-8') as file:
        file.write(cleaned_text)
    
    # Comprobar si el archivo de transcripción existe y procesar
    if os.path.exists('ted_transcript.txt'):
        with open('ted_transcript.txt', 'r', encoding='utf-8') as f:
            transcript_to_process = f.read()
        
        # Generar el resumen utilizando la función de resumen
        final_summary = ted_summarize_text(transcript_to_process)
        
        # Guardar el resumen en un archivo
        with open('ted_summary.txt', 'w', encoding='utf-8') as f:
            f.write(final_summary)
        
        return final_summary
    else:
        raise FileNotFoundError("Error: File ted_transcript.txt not found.")
'''