import os

UPLOAD_FOLDER = 'uploads'

def save_file_locally(file_obj, filename):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file_path = os.path.join(UPLOAD_FOLDER, filename.replace(' ', '_'))
    file_obj.save(file_path)
    return file_path
