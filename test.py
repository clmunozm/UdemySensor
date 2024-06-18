import requests

# Reemplaza este valor con tu propio token de acceso personal
access_token = ""

# Prepara los headers para la solicitud
headers = {
    'Authorization': f'Bearer {access_token}',
}

# Función para obtener los cursos inscritos
def get_subscribed_courses():
    response = requests.get('https://www.udemy.com/api-2.0/users/me/subscribed-courses/', headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error al obtener los cursos inscritos:", response.status_code, response.text)
        return None

# Función para obtener el progreso de un curso
def get_course_progress(course_id):
    response = requests.get(f'https://www.udemy.com/api-2.0/users/me/subscribed-courses/{course_id}/progress/', headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error al obtener el progreso del curso {course_id}:", response.status_code, response.text)
        return None

# Obtener los cursos inscritos
courses = get_subscribed_courses()
if courses:
    for course in courses['results']:
        course_id = course['id']
        course_title = course['title']
        print(f"Curso: {course_title} (ID: {course_id})")

        # Obtener el progreso del curso
        progress = get_course_progress(course_id)
        if progress:
            print(f"Progreso en {course_title}: {progress}")
