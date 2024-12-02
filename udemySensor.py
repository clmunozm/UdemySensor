import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from tkinter import PhotoImage
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
            messagebox.showwarning("Error 403", "Error 403:Permiso denegado. El token de acceso podría ser inválido.")
            return 403
        else:
            print("Error al obtener los cursos inscritos:", response.status_code, response.text)
            messagebox.showwarning("Error", "Error al obtener los cursos inscritos")
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
        print(f"Error to obtain course progress {course_id}:", response.status_code, response.text)
        return None

# Cargar el progreso anterior desde el archivo
def load_previous_progress():
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            all_progress = json.load(f)
            # Retorna el progreso del user_id actual si existe
            return all_progress.get(str(user_id), {})
    return {}

# Guardar el progreso actual en el archivo, incluyendo el user_id
def save_progress(progress):
    all_progress = {}
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            all_progress = json.load(f)
    
    all_progress[str(user_id)] = progress  # Asocia el progreso con el user_id actual
    
    with open(progress_file, 'w') as f:
        json.dump(all_progress, f, indent=4)

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

    # Guardar progreso solo si hubo cambios
    if new_progress:
        save_progress(new_progress)
    
    return total_points

# Función para calcular puntos basados en el progreso incremental
def calculate_incremental_points(course_id, current_percentage, previous_percentage):
    if (current_percentage > previous_percentage):
        points = (current_percentage // 10) - (previous_percentage // 10)
        return max(points, 0)
    else:
        return 0

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

class LoginDialog(simpledialog.Dialog):
    def __init__(self, master, title=None):
        self.style = ttk.Style()
        self.style.theme_use("clam")  # Tema moderno
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=("Helvetica", 12))
        self.style.configure("TEntry", font=("Helvetica", 11))
        self.style.configure("TButton", background="#007BFF", foreground="#ffffff", font=("Helvetica", 12))
        super().__init__(master, title=title)

    def body(self, master):
        self.configure(bg='#f0f0f0')  # Fondo de la ventana

        frame = ttk.Frame(master, padding=20)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Username:").grid(row=0, column=0, pady=5, sticky="w")
        self.username_entry = ttk.Entry(frame, style="TEntry", width=30)
        self.username_entry.grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="Password:").grid(row=1, column=0, pady=5, sticky="w")
        self.password_entry = ttk.Entry(frame, style="TEntry", show="*", width=30)
        self.password_entry.grid(row=1, column=1, pady=5)

        return self.username_entry

    def buttonbox(self):
        box = ttk.Frame(self, style="TFrame")
        box.pack(side="bottom", fill="x", padx=5, pady=5)

        authenticate_button = ttk.Button(box, text="Login", command=self.ok)
        authenticate_button.pack(side="left", padx=(5, 0), pady=5)

        cancel_button = ttk.Button(box, text="Cancel", command=self.cancel)
        cancel_button.pack(side="right", padx=(0, 5), pady=5)

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
    # Cargar imagen de icono
    icon = PhotoImage(file='icon.png')
    # Asignar el icono a la ventana
    root.iconphoto(True, icon)  # True asegura que el icono se asigna correctamente
    # Pasar el título al cuadro de diálogo de inicio de sesión
    while True:
        dialog = LoginDialog(root, title="Login bGames")
        username = dialog.username
        password = dialog.password

        if not username or not password:
            messagebox.showwarning("Input Error", "Username and Password cannot be empty.")
        else:
            break
        
    root.destroy()

    try:
        response = requests.get(f"{player_endpoint}{username}/{password}")
        if response.status_code == 200:
            user_id = response.json()
            if user_id:
                print(f"Usuario autenticado. User ID: {user_id}")
            else:
                messagebox.showerror("Error", "")
        else:
            messagebox.showerror("Error", f"Invalid credentials or unable to reach the server.")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Unable to reach the server: {str(e)}")


def ask_for_token():
    def submit_token():
        token = token_entry.get().strip()
        if not token:
            messagebox.showerror("Error", "Please, enter a valid token.")
        else:
            nonlocal access_token
            access_token = token
            token_window.destroy()

    # Ventana principal para el token
    token_window = tk.Tk()
    token_window.title(" Access Token")
    token_window.configure(bg='#f0f0f0')
    # Cargar imagen de icono
    icon = PhotoImage(file='icon.png')
    # Asignar el icono a la ventana
    token_window.iconphoto(True, icon)  # True asegura que el icono se asigna correctamente
    # Configuración de estilos personalizados
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TFrame", background="#f0f0f0")
    style.configure("TLabel", background="#f0f0f0", font=("Helvetica", 12))
    style.configure("TEntry", font=("Helvetica", 11))
    style.configure("TButton", background="#007BFF", foreground="#ffffff", font=("Helvetica", 12, "bold"))

    # Centrar la ventana
    window_width, window_height = 400, 200
    screen_width, screen_height = token_window.winfo_screenwidth(), token_window.winfo_screenheight()
    position_top = int(screen_height / 2 - window_height / 2)
    position_right = int(screen_width / 2 - window_width / 2)
    token_window.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

    # Frame principal
    frame = ttk.Frame(token_window, padding=20)
    frame.pack(expand=True)

    ttk.Label(frame, text="Enter your udemy token:").pack(pady=(10, 5))
    
    token_entry = ttk.Entry(frame, width=30)
    token_entry.pack(pady=5)

    submit_button = ttk.Button(frame, text="Continue", command=submit_token)
    submit_button.pack(pady=10)

    cancel_button = ttk.Button(frame, text="Cancel", command=token_window.destroy)
    cancel_button.pack(pady=(0, 5))

    access_token = None
    token_window.mainloop()

    if access_token is None:
        messagebox.showerror("Cancelado", "El programa se cerrará ya que no se proporcionó un token de acceso.")
        exit()

    return access_token

class LoadingWindow(tk.Toplevel):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.title("Loading...")
        self.configure(bg='#f0f0f0')
        # Cargar imagen de icono
        icon = PhotoImage(file='icon.png')
        # Asignar el icono a la ventana
        self.iconphoto(True, icon)  # True asegura que el icono se asigna correctamente
        # Configuración de estilos personalizados
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0", font=("Helvetica", 14))

        # Frame contenedor
        frame = ttk.Frame(self, padding=20, style="TFrame")
        frame.pack(fill="both", expand=True)

        # Etiqueta de carga
        self.label = ttk.Label(frame, text="Loading Udemy courses...", style="TLabel")
        self.label.pack(pady=20)

        # Manejo del cierre de la ventana
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.destroy()

# Clase para la ventana de progreso
class ProgressWindow(tk.Toplevel):
    def __init__(self, master, course_data, total_points, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.title("Udemy Courses Progress Sensor")
        self.configure(bg='#f0f0f0')

        # Cargar imagen de icono
        icon = PhotoImage(file='icon.png')
        # Asignar el icono a la ventana
        self.iconphoto(True, icon)  # True asegura que el icono se asigna correctamente

        # Configuración de estilos personalizados
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0", font=("Helvetica", 14))
        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", font=("Helvetica", 12))
        style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"))
        style.map("Treeview", background=[("selected", "#007BFF")], foreground=[("selected", "#ffffff")])

        # Manejo del cierre de la ventana
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Etiqueta de carga
        self.loading_label = ttk.Label(self, text="Udemy Data", style="TLabel")
        self.loading_label.pack(pady=(10, 5))

        # Frame para el Treeview
        self.courses_frame = ttk.Frame(self, padding=10)
        self.courses_frame.pack(fill="both", expand=True)

        # Treeview con columnas personalizadas
        self.tree = ttk.Treeview(
            self.courses_frame, 
            columns=("course", "progress", "points"), 
            show="headings", 
            selectmode="browse"
        )
        self.tree.heading("course", text="Courses")
        self.tree.heading("progress", text="Progress (%)")
        self.tree.heading("points", text="Points")
        self.tree.column("course", anchor="w", width=200)
        self.tree.column("progress", anchor="center", width=100)
        self.tree.column("points", anchor="center", width=100)

        # Scrollbar para Treeview
        scrollbar = ttk.Scrollbar(self.courses_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.tree.pack(fill="both", expand=True, pady=5, padx=5)

        # Cargar los datos en el Treeview
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
    courses = get_subscribed_courses()

    if courses == 403:
        while True:
            access_token = ask_for_token()
            headers = {
                'Authorization': f'Bearer {access_token}',
            }
            courses = get_subscribed_courses()
            if courses != 403:
                break
    elif not courses:
        print("No se pudieron obtener los cursos inscritos. Saliendo del programa.")
        exit()

    root = tk.Tk()
    root.withdraw()

    # Cargando cursos y calculando progreso y puntos antes de abrir ProgressWindow
    loading_window = LoadingWindow(root)
    loading_window.update()

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
