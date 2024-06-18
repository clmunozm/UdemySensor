import requests
import base64

# Reemplaza estos valores con tus propios Client ID y Client Secret
client_id = ""
client_secret = ""

# Combina el Client ID y el Client Secret con un dos puntos entre ellos
credentials = f"{client_id}:{client_secret}"

# Codifica la cadena resultante en Base64
encoded_credentials = base64.b64encode(credentials.encode()).decode()

# Prepara los headers para la solicitud
headers = {
    'Authorization': f'Basic {encoded_credentials}',
}

# Realiza la solicitud GET a la API de Udemy
response = requests.get('https://www.udemy.com/api-2.0/courses/4463684', headers=headers)

# Verifica la respuesta
if response.status_code == 200:
    # Procesa la respuesta
    print(response.json())
else:
    print("Error al obtener los datos:", response.status_code, response.text)
