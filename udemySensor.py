import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import threading
import requests
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

# Función para obtener todos los cursos inscritos manejando la paginación
def get_subscribed_courses():
    courses = []
    next_url = 'https://www.udemy.com/api-2.0/users/me/subscribed-courses/'

    while next_url:
        response = requests.get(next_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            courses.extend(data['results'])
            next_url = data.get('next')  # URL para la siguiente página
        elif response.status_code == 403:
            print("Error 403: Permiso denegado. El token de acceso podría ser inválido.")
            return None
        else:
            print("Error al obtener los cursos inscritos:", response.status_code, response.text)
            return None
    return courses

# Función para obtener el progreso de un curso
def get_course_progress(course_id):
    response = requests.get(f'https://www.udemy.com/api-2.0/users/me/subscribed-courses/{course_id}/progress/', headers=headers)
    if response.status_code == 200:
        progress = response.json()
        completion_percentage = progress.get('completion_ratio', 0)
        return completion_percentage
    else:
        print(f"Error al obtener el progreso del curso {course_id}:", response.status_code, response.text)
        return None

# Cargar el progreso anterior desde el archivo
def load_previous_progress():
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            previous_progress = json.load(f)
            return previous_progress
    return {}

# Guardar el progreso actual en el archivo
def save_progress(progress):
    with open(progress_file, 'w') as f:
        json.dump(progress, f)

# Función para calcular puntos basados en el progreso incremental
def calculate_incremental_points(course_id, current_percentage, previous_percentage):
    points = (current_percentage // 10) - (previous_percentage // 10)
    return max(points, 0)

# Función para obtener el total de puntos de todos los cursos
def get_total_points(courses, previous_progress):
    total_points = 0
    new_progress = {}

    for course in courses:
        course_id = str(course['id'])
        current_percentage = get_course_progress(course_id)
        if current_percentage is not None:
            previous_percentage = previous_progress.get(course_id, 0)
            points = calculate_incremental_points(course_id, current_percentage, previous_percentage)
            total_points += points
            new_progress[course_id] = current_percentage
    
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
# Clase para el diálogo de inicio de sesión
class LoginDialog(simpledialog.Dialog):
    def __init__(self, master, title=None):
        super().__init__(master, title=title)

    def body(self, master):
        tk.Label(master, text="Nombre de Usuario:").grid(row=0)
        tk.Label(master, text="Contraseña:").grid(row=1)
        
        self.username_entry = tk.Entry(master)
        self.password_entry = tk.Entry(master, show="*")
        self.username_entry.grid(row=0, column=1)
        self.password_entry.grid(row=1, column=1)
        return self.username_entry

    def apply(self):
        self.username = self.username_entry.get()
        self.password = self.password_entry.get()

# Función para solicitar el nombre de usuario y contraseña
def ask_for_credentials():
    global user_id
    
    root = tk.Tk()
    root.withdraw()
    
    # Establecer el nombre de la ventana principal
    root.title("Inicio de Sesión")
    
    # Pasar el título al cuadro de diálogo de inicio de sesión
    dialog = LoginDialog(root, title="Por favor, ingrese sus credenciales")
    username = dialog.username
    password = dialog.password

    if not username or not password:
        messagebox.showerror("Cancelado", "El programa se cerrará ya que no se proporcionaron credenciales.")
        exit()
    
    root.destroy()

    try:
        response = requests.get(f"{player_endpoint}{username}/{password}")
        if response.status_code == 200:
            user_id = response.json()
            if user_id:
                print(f"Usuario autenticado. User ID: {user_id}")
            else:
                messagebox.showerror("Error", "No se pudo obtener el userId del servidor.")
        else:
            messagebox.showerror("Error", f"Error al autenticar: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error de Conexión", f"No se pudo conectar al servidor: {str(e)}")
# Función para solicitar el token de acceso mediante una interfaz gráfica
def ask_for_token():
    while True:
        root = tk.Tk()
        root.withdraw()

        access_token = simpledialog.askstring("Token de Acceso", "Por favor, introduce tu token de acceso Udemy:")

        if access_token is None:
            messagebox.showerror("Cancelado", "El programa se cerrará ya que no se proporcionó un token de acceso.")
            root.destroy()
            exit()

        else:
            root.destroy()
            return access_token

# Clase para la ventana de carga
class LoadingWindow(tk.Toplevel):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.title("Cargando")
        self.label = tk.Label(self, text="Cargando Cursos desde Udemy...", font=("Arial", 14))
        self.label.pack(pady=20)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.quit()
        self.destroy()

# Clase para la ventana de progreso
class ProgressWindow(tk.Toplevel):
    def __init__(self, master, course_data, total_points, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.title("Udemy courses progress sensor")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.loading_label = tk.Label(self, text="Datos cargados", font=("Arial", 14))
        self.loading_label.pack(pady=10)

        self.courses_frame = tk.Frame(self)
        self.courses_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(self.courses_frame, columns=("course", "progress", "points"), show="headings")
        self.tree.heading("course", text="Curso")
        self.tree.heading("progress", text="Progreso (%)")
        self.tree.heading("points", text="Puntos")
        self.tree.pack(fill="both", expand=True, pady=10, padx=10)

        # Cargar los datos calculados en la ventana
        for course in course_data:
            self.tree.insert("", "end", values=course)

    def on_close(self):
        self.quit()
        self.destroy()

# Función modificada para mostrar la ventana de progreso
def main():
    global headers, user_id

    ask_for_credentials()

    if not user_id:
        print("No se obtuvo un userId válido. Saliendo del programa.")
        exit()

    access_token = ask_for_token()

    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    root = tk.Tk()
    root.withdraw()

    # Cargando cursos y calculando progreso y puntos antes de abrir ProgressWindow
    loading_window = LoadingWindow(root)
    loading_window.update()

    courses = get_subscribed_courses()

    if courses:
        previous_progress = load_previous_progress()

        # Calcula el progreso y los puntos aquí
        new_progress = {}
        total_points = 0
        course_data = []

        for course in courses:
            course_id = str(course['id'])
            current_percentage = get_course_progress(course_id)
            if current_percentage is not None:
                previous_percentage = previous_progress.get(course_id, 0)
                points = calculate_incremental_points(course_id, current_percentage, previous_percentage)
                new_progress[course_id] = current_percentage
                total_points += points

                # Guarda la información del curso para pasarla a ProgressWindow
                course_data.append((course['title'], current_percentage, points))

        loading_window.destroy()
        save_progress(new_progress)

        # Ahora pasa la data ya calculada a la ProgressWindow
        progress_window = ProgressWindow(root, course_data, total_points)
        progress_window.mainloop()

        # Enviar puntos si se calculó algún punto
        if total_points > 0:
            send_points(total_points, user_id, "5")
    else:
        messagebox.showerror("Error", "No se pudieron obtener los cursos inscritos.")
        exit()

    root.quit()


if __name__ == "__main__":
    main()
