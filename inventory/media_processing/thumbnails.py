import os.path
from io import BytesIO
from PIL import Image

from pdf2image import convert_from_bytes
from django.core.files.base import ContentFile


def generate_thumbnail_name(filename):
    unique_name = os.path.splitext(os.path.basename(filename))[0]

    return f"{unique_name}-thumb.jpg"


def generate_image_thumbnail(file_field, size=(300, 300)):
    img = Image.open(file_field)
    img = img.convert("RGB")
    img.thumbnail(size, Image.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=85)

    return ContentFile(buffer.getvalue())


def generate_pdf_thumbnail(file_field, size=(600, 600)):
    images = convert_from_bytes(
        file_field.read(),
        first_page=1,
        last_page=1,
        size=size,
    )

    buffer = BytesIO()
    images[0].save(buffer, format="JPEG", quality=85)

    return ContentFile(buffer.getvalue())
