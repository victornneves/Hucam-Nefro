import requests

api_whisper_ip = "http://localhost:5000"


patient = 18
chunkNumber = 30

url = api_whisper_ip + f"/getWhisperChunk?patient={patient}&chunkNumber={chunkNumber}"

with requests.Session() as s:
    result = s.get(url)
    result = result.json()
    print(result["content"])