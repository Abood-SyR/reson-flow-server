import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def upload_to_cloudinary(file_obj, folder="reson_flow"):
    if not file_obj or not file_obj.filename:
        return None
    try:
        result = cloudinary.uploader.upload(file_obj.file, folder=folder, resource_type="auto")
        return result.get("secure_url")
    except Exception as e:
        return None