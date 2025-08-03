import os

UPLOAD_FOLDER = 'uploads'

def save_file_locally(file_obj, filename):
    """
    Saves a file-like object to the local uploads folder.

    Args:
        file_obj: The file object received (e.g., Flask's UploadedFile).
        filename: The original filename string.

    Returns:
        The full file path where the file was saved.
    """
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Create folder if not exists
    safe_filename = filename.replace(' ', '_')  # Replace spaces to prevent filesystem issues
    file_path = os.path.join(UPLOAD_FOLDER, safe_filename)

    # Save the uploaded file object to this path
    file_obj.save(file_path)

    return file_path
