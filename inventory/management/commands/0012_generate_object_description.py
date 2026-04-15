from django.core.management.base import BaseCommand
from django.db.models import Q

from inventory.models import Document

from pprint import pprint


class Command(BaseCommand):
    help = "Generate derived related_object text field from related content."

    def handle(self, *args, **options):
        self.stdout.write("Processing documents...")
        count = 0

        # for obj in Document.objects.all():
        for obj in Document.objects.filter(
            Q(object_description__isnull=True) | Q(object_description="")
        ).iterator(chunk_size=50):
            object_description = obj.context_object_display()
            print(object_description)
            obj.object_description = object_description
            obj.save(update_fields=["object_description"])
            count += 1
            if count % 50 == 0:
                self.stdout.write(f"Processed {count} items...")

        self.stdout.write(self.style.SUCCESS("Done"))
