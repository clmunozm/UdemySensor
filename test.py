import tkinter as tk
from tkinter import simpledialog, messagebox
import requests
import time
import json
import os

# Archivo para guardar el progreso anterior
progress_file = "previous_progress.json"

# URL del endpoint para obtener el userId
player_endpoint = "http://localhost:3010/player/"

# URL del endpoint para enviar los puntos
points_endpoint = "http://localhost:3002/adquired_subattribute/"

# Prepara los headers para la solicitud
headers = {}

# Variable global para almacenar el userId
user_id = None

# Función para obtener los cursos inscritos
def get_subscribed_courses():
    response = requests.get('https://www.udemy.com/api-2.0/users/me/subscribed-courses/', headers=headers)
    if response.status_code == 200:
        courses = response.json()
        print("Cursos inscritos obtenidos:")
        for course in courses['results']:
            print(f" - {course['title']} (ID: {course['id']})")
        return courses
    elif response.status_code == 403:
        print("Error 403: Permiso denegado. El token de acceso podría ser inválido.")
        return "403"
    else:
        print("Error al obtener los cursos inscritos:", response.status_code, response.text)
        return None

# Función para obtener el progreso de un curso
def get_course_progress(course_id):
    response = requests.get(f'https://www.udemy.com/api-2.0/users/me/subscribed-courses/{course_id}/progress/', headers=headers)
    if response.status_code == 200:
        progress = response.json()
        # Usamos el valor entero directamente ya que representa el porcentaje de completitud
        completion_percentage = progress.get('completion_ratio', 0)
        print(f"Progreso del curso {course_id} obtenido: {completion_percentage}%")
        return completion_percentage
    else:
        print(f"Error al obtener el progreso del curso {course_id}:", response.status_code, response.text)
        return None

# Cargar el progreso anterior desde el archivo
def load_previous_progress():
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            previous_progress = json.load(f)
            print("Progreso anterior cargado:", previous_progress)
            return previous_progress
    return {}

# Guardar el progreso actual en el archivo
def save_progress(progress):
    with open(progress_file, 'w') as f:
        json.dump(progress, f)
    print("Progreso actualizado guardado:", progress)

# Función para calcular puntos basados en el progreso incremental
def calculate_incremental_points(course_id, current_percentage, previous_percentage):
    # Calcular los puntos basados en el rango de 10% completado
    points = (current_percentage // 10) - (previous_percentage // 10)

    print(f"Curso ID {course_id}: Progreso anterior: {previous_percentage}%, Progreso actual: {current_percentage}%, Puntos otorgados: {points}")

    # Asegurarse de no otorgar puntos negativos
    return max(points, 0)

# Función para obtener el total de puntos de todos los cursos
def get_total_points(courses, previous_progress):
    total_points = 0
    new_progress = {}

    for course in courses['results']:
        course_id = str(course['id'])
        current_percentage = get_course_progress(course_id)
        if current_percentage is not None:
            previous_percentage = previous_progress.get(course_id, 0)
            points = calculate_incremental_points(course_id, current_percentage, previous_percentage)
            if points > 0:
                print(f"Se han otorgado {points} puntos por el curso '{course['title']}' (ID: {course_id}).")
            total_points += points
            new_progress[course_id] = current_percentage
    
    # Guardar el nuevo progreso para futuras comparaciones
    save_progress(new_progress)
    
    return total_points

# Función para enviar los puntos al endpoint
def send_points(total_points, player_id, sensor_endpoint_id):
    url = points_endpoint
    data = {
        "id_player": player_id,
        "id_subattributes_conversion_sensor_endpoint": sensor_endpoint_id,
        "new_data": [str(total_points)]
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print(f"Puntos enviados exitosamente: {total_points}")
    else:
        print(f"Error al enviar puntos: {response.status_code} - {response.text}")

# Función para solicitar el token de acceso mediante una interfaz gráfica
def ask_for_token():
    while True:
        root = tk.Tk()
        root.withdraw()  # Oculta la ventana principal

        access_token = simpledialog.askstring("Token de Acceso", "Por favor, introduce tu token de acceso Udemy:")

        if access_token is None:  # El usuario presionó "Cancelar"
            messagebox.showerror("Cancelado", "El programa se cerrará ya que no se proporcionó un token de acceso.")
            root.destroy()
            exit()

        root.destroy()

        # Intenta verificar el token ingresado
        headers['Authorization'] = f'Bearer {access_token}'
        test_response = get_subscribed_courses()

        if test_response != "403":
            return access_token
        else:
            messagebox.showerror("Token Inválido", "El token de acceso ingresado no es válido. Por favor, intenta nuevamente.")
            print("Solicitando nuevo token de acceso...")

# Función para solicitar el nombre de usuario y contraseña mediante una interfaz gráfica
def ask_for_credentials():
    global user_id
    
    root = tk.Tk()
    root.withdraw()  # Oculta la ventana principal
    
    username = simpledialog.askstring("Inicio de Sesión", "Nombre de Usuario:")
    if username is None:  # El usuario presionó "Cancelar"
        messagebox.showerror("Cancelado", "El programa se cerrará ya que no se proporcionó un nombre de usuario.")
        root.destroy()
        exit()
    
    password = simpledialog.askstring("Inicio de Sesión", "Contraseña:", show="*")
    if password is None:  # El usuario presionó "Cancelar"
        messagebox.showerror("Cancelado", "El programa se cerrará ya que no se proporcionó una contraseña.")
        root.destroy()
        exit()
    
    root.destroy()

    # Enviar datos al endpoint para obtener el userId
    try:
        response = requests.get(f"{player_endpoint}{username}/{password}")
        if response.status_code == 200:
            user_id = response.json()  # Asignamos el userId obtenido
            if user_id:
                print(f"Usuario autenticado. User ID: {user_id}")
            else:
                messagebox.showerror("Error", "No se pudo obtener el userId del servidor.")
        else:
            messagebox.showerror("Error", f"Error al autenticar: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error de Conexión", f"No se pudo conectar al servidor: {str(e)}")

# Función principal para obtener los cursos y enviar puntos
def main():
    global headers, user_id
    
    # Solicitar credenciales y obtener el userId
    ask_for_credentials()
    
    if not user_id:
        print("No se obtuvo un userId válido. Saliendo del programa.")
        exit()

    player_id = str(user_id)  # ID del jugador (convertido a string)
    sensor_endpoint_id = "5"  # ID del endpoint del sensor

    # Solicitar el token de acceso
    access_token = ask_for_token()
    
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    
    while True:
        courses = get_subscribed_courses()
        if courses and courses != "403":
            previous_progress = load_previous_progress()
            total_points = get_total_points(courses, previous_progress)
            print(f"Total de puntos obtenidos: {total_points}")
            if total_points > 0:
                send_points(total_points, player_id, sensor_endpoint_id)
        time.sleep(3600)  # Esperar 1 hora antes de volver a ejecutar

# Ejecutar la función principal
if __name__ == "__main__":
    main()
