from django.core.management.base import BaseCommand
from django.db.models import Q

from inventory.models import Photo, Document
from inventory.media_processing.thumbnails import (
    generate_image_thumbnail,
    generate_pdf_thumbnail,
    generate_thumbnail_name,
)


class Command(BaseCommand):
    help = "Generate thumbnails for existing media"

    def handle(self, *args, **options):
        self.stdout.write("Processing photos...")
        count = 0

        for obj in Photo.objects.filter(
            Q(thumbnail__isnull=True) | Q(thumbnail="")
        ).iterator(chunk_size=50):
            thumb = generate_image_thumbnail(obj.photo)
            unique_name = generate_thumbnail_name(obj.photo.name)
            obj.thumbnail.save(unique_name, thumb, save=False)
            obj.save(update_fields=["thumbnail"])
            count += 1
            if count % 50 == 0:
                self.stdout.write(f"Processed {count} items...")

        self.stdout.write("Processing documents...")
        count = 0

        for obj in Document.objects.filter(
            Q(thumbnail__isnull=True) | Q(thumbnail="")
        ).iterator(chunk_size=50):
            thumb = generate_pdf_thumbnail(obj.file)
            unique_name = generate_thumbnail_name(obj.file.name)
            obj.thumbnail.save(unique_name, thumb, save=False)
            obj.save(update_fields=["thumbnail"])
            count += 1
            if count % 50 == 0:
                self.stdout.write(f"Processed {count} items...")

        self.stdout.write(self.style.SUCCESS("Done"))
