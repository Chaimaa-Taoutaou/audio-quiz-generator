import requests
import streamlit as st
import sounddevice as sd
import soundfile as sf
import librosa
import speech_recognition as sr
import tempfile
import os
import openai
import toml
from oauth2client import client, file, tools
from apiclient import discovery
from httplib2 import Http
from PIL import Image
import config


ques = []

st.set_page_config(
        page_title="Quiz Generator",
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
# Add custom CSS styles to the sidebar
st.markdown(
    """
    <style>
    .css-ulqv4t{
        background-color: red;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Add content to the sidebar
st.sidebar.header('Home')
st.sidebar.header('Quiz')


st.title("Audio Recording and Google Forms Generator App")
st.write("Greetings! You have arrived at the application where you can effortlessly capture audio and create Google Forms quizzes. You are encouraged to select your preferred language for the recording process.")
image = Image.open('image_2.jpg')
col1,col2 = st.columns(2)
col1.image(image,width=700,use_column_width=True)

def create_form():   
    SCOPES = "https://www.googleapis.com/auth/forms.body"
    DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"
    store = file.Storage('token.json')
    creds = None
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client.json', SCOPES)
        creds = tools.run_flow(flow, store)

    form_service = discovery.build('forms', 'v1', http=creds.authorize(
        Http()), discoveryServiceUrl=DISCOVERY_DOC, static_discovery=False)

    # Request body for creating a form
    NEW_FORM = {
        "info": {
            "title": "Quiz",
        }
    }
    # Request body to add a multiple-choice question
    NEW_QUESTION = {
    "requests": []
    }
    for i in range(len(ques)):
        question = ques[i]
        options = resp[i]
        create_item = {
            "createItem": {
                "item": {
                    "title": question,
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": [
                                    {"value": option} for option in options
                                ],
                                "shuffle": True
                            }
                        }
                    }
                },
                "location": {
                    "index": 0
                }
            }
        }

        NEW_QUESTION["requests"].insert(0, create_item)
        # Creates the initial form
        result = form_service.forms().create(body=NEW_FORM).execute()
        responder_uri = result['responderUri']
        # Adds the question to the form
        question_setting = form_service.forms().batchUpdate(formId=result["formId"], body=NEW_QUESTION).execute()
    return responder_uri

# Liste des langages supportés
languages = {
    "fr-FR": "Français",
    "en-US": "English",
    "es-ES": "Español",
    "ar": "العربية" 
}




def record_audio(duration):
    # Set the sample rate and channels for recording
    sample_rate = 44100  # CD quality audio
    channels = 2        # Stereo

    
    # Start recording audio
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels)

    # Wait for the recording to finish
    sd.wait()

    return audio, sample_rate

def save_audio(audio, sample_rate, filepath):
    # Save the recorded audio to a file
    sf.write(filepath, audio, sample_rate)


def convert_audio_to_text(filepath, lang="fr-FR"):
    r = sr.Recognizer()

    with sr.AudioFile(filepath) as source:
        audio_data = r.record(source)
        texte = r.recognize_google(audio_data, language=lang)

    return texte

# use chatGPT API 







# Set title with custom styling
st.title("Voice Recorder")
st.markdown(
    """
    <style>
    .title {
        color: #1f2937;
        font-size: 36px;
        font-weight: bold;
        margin-bottom: 30px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Demande à l'utilisateur de choisir la langue
selected_lang = st.selectbox("Choose the language:", list(languages.values()))

# Récupère le code de langue correspondant
lang_code = [k for k, v in languages.items() if v == selected_lang][0]

# Set selectbox styling
st.markdown(
    """
    <style>
    .select-box {
        background-color: #ffffff;
        border: 1px solid #e4e7eb;
        border-radius: 5px;
        padding: 10px;
        color: #1f2937;
        font-size: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# User input for recording duration
duration = st.number_input("Recording duration (seconds)", min_value=1.0, value=5.0, step=1.0)

# Set number input styling
st.markdown(
    """
    <style>
    .number-input {
        background-color: #ffffff;
        border: 1px solid #e4e7eb;
        border-radius: 5px;
        padding: 10px;
        color: #1f2937;
        font-size: 16px;
    }
    .number-input input[type="number"] {
        appearance: textfield;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# define a variable wish contains the text generated from the voice 
texte=""
# Initialize prompt in session state
if "prompt" not in st.session_state:
    st.session_state["prompt"] = ""
    # Start/stop recording button
if st.button("Record"):
    st.info("Recording...")

        # Record audio
    audio, sample_rate = record_audio(duration)

    st.success("Recording complete!")

        # Save recorded audio to a file

    filepath = st.text_input("", "recorded_audio.wav")
    save_audio(audio, sample_rate, filepath)

    st.audio(filepath, format='audio/wav')
    texte = convert_audio_to_text(filepath, lang=lang_code)
    st.header("Transcribed Text")
    st.write(texte)
    st.session_state["prompt"] = texte

#Use chtagpt API 
api_key = config.API_KEY
openai.api_key = config.API_KEY
BASE_PROMPT = [{"role": "system", "content": "You are a helpful assistant."}]

if "messages" not in st.session_state:
    st.session_state["messages"] = BASE_PROMPT

st.title("Generate the Quiz")
    
text = st.empty()

#prompt = st.text_input("Prompt", value=texte)
#print(prompt)



def generate_questions(prompt):
            api_endpoint = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": "Bearer " + api_key,
                "Content-Type": "application/json"
            }
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
            response = requests.post(api_endpoint, headers=headers, json=data)
            if response.status_code == 200:
                questions = response.json()["choices"]
                return questions
            else:
                return None

if st.button("Generate Questions"):
                prompt = st.session_state["prompt"]
                questions = generate_questions("generate a quiz about machine learning")
                if questions:
                    content = questions[0]["message"]["content"]

                    resp = []

                    # Split the data based on the question numbering
                    question_data = content.split('\n\n')

                    for item in question_data:
                        item = item.strip()  # Remove leading/trailing spaces
                        if item:
                            parts = item.split('\n', 1)  # Split into question and choices
                            if len(parts) == 2:
                                question, choices = parts
                                question = question.strip()  # Remove leading/trailing spaces from the question
                                choices = choices.split('\n')  # Split choices into a list
                                choices = [choice.strip() for choice in choices]  # Remove leading/trailing spaces from choices
                                ques.append(question)
                                resp.append(choices)
                    st.write(create_form())
