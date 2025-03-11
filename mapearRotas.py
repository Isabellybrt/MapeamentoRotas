import os
import requests
import speech_recognition as sr
from google.cloud import texttospeech
import json


base_dir = os.path.dirname(os.path.abspath(__file__))
cred_path = os.path.join(base_dir, ".gcp", "hazel-thunder-433817-c4-cedb9662b24d.json")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path


api_key = "colocar chave API"
print(f"API Key: {api_key}")  # Verifique se a chave está sendo carregada corretamente


def get_current_location():
    try:
        send_url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={api_key}"
        r = requests.post(send_url, json={})  # Agora enviando um JSON vazio
        j = r.json()
        print("Resposta da API de geolocalização:", j)  # Debug

        lat = j['location']['lat']
        lng = j['location']['lng']
        return f"{lat},{lng}"
    except Exception as e:
        print(f"Erro ao obter localização atual: {e}")
        return None


def get_directions(api_key, origin, destination):
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "routes.legs.steps.navigationInstruction.instructions"
    }

    data = {
        "origin": {"location": {"latLng": {"latitude": float(origin.split(",")[0]), "longitude": float(origin.split(",")[1])}}},
        "destination": {"location": {"latLng": {"latitude": float(destination.split(",")[0]), "longitude": float(destination.split(",")[1])}}},
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_AWARE",
        "computeAlternativeRoutes": False
    }

    response = requests.post(url, headers=headers, json=data)
    directions = response.json()
    
    print("Resposta da API de direções:", json.dumps(directions, indent=2))

    if "routes" in directions and "legs" in directions["routes"][0]:
        steps = directions["routes"][0]["legs"][0]["steps"]
        directions_text = [step["navigationInstruction"]["instructions"] for step in steps]
        return directions_text
    else:
        return ["Não foi possível obter direções."]

    
def get_coordinates_from_address(address):
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
        response = requests.get(url)
        data = response.json()
        
        if data["status"] == "OK":
            location = data["results"][0]["geometry"]["location"]
            return f"{location['lat']},{location['lng']}"
        else:
            print(f"Erro ao obter coordenadas: {data['status']}")
            return None
    except Exception as e:
        print(f"Erro na geocodificação: {e}")
        return None


def get_voice_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Diga o seu destino:")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    
    try:
        command = recognizer.recognize_google(audio, language="pt-BR")
        return command
    except sr.UnknownValueError:
        return "Não entendi o comando"
    except sr.RequestError:
        return "Erro na solicitação ao serviço de reconhecimento de voz"

def text_to_speech(text):
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="pt-BR",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    # Salvar e tocar áudio corretamente
    audio_path = "output.wav"
    with open(audio_path, "wb") as out:
        out.write(response.audio_content)

    os.system(f"aplay {audio_path}")  # No Windows, pode usar playsound

def main():
    origin = get_current_location()
    if origin:
        destination_name = get_voice_command()
        print(f"Destino reconhecido: {destination_name}")

        if destination_name and destination_name not in ["Não entendi o comando", "Erro na solicitação ao serviço de reconhecimento de voz"]:
            destination = get_coordinates_from_address(destination_name)

            if destination:
                directions = get_directions(api_key, origin, destination)
                print("Instruções de rota:")
                instructions_text = " ".join(directions)
                print(instructions_text)

                text_to_speech(instructions_text)
            else:
                print("Não foi possível obter as coordenadas do destino.")
        else:
            print("Destino inválido. Tente novamente.")


if __name__ == "__main__":
    main()
