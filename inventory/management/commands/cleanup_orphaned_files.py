# myapp/management/commands/cleanup_orphaned_files.py

"""A few things worth noting:

Always do a dry run first. The --dry-run flag is there precisely so
you can audit what would be removed before committing. It's easy to
misconfigure a path and accidentally match files you didn't intend to.

Scope the walk to your upload subdirectory. Rather than walking all of
MEDIA_ROOT, scope it to the specific subfolder your FileField uploads
into (e.g. documents/). This avoids accidentally touching unrelated
files in media that your app doesn't manage.

If you have multiple models with FileFields, extend the command to
build known_files from all of them before doing the walk:

from myapp.models import Document, Equipment  # etc.

known_files = set()
known_files.update(Document.objects.exclude(file='').values_list('file', flat=True))
# add other models here as needed
"""

import os
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings
from inventory.models import Document, Photo


class Command(BaseCommand):
    help = "Remove uploaded files not referenced by any Document or Photo record"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report orphaned files without deleting them",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        media_root = Path(settings.MEDIA_ROOT)

        # Collect all file paths the DB knows about, across all four fields
        known_files = set()
        known_files.update(
            Document.objects.exclude(file="").values_list("file", flat=True)
        )
        known_files.update(
            Document.objects.exclude(thumbnail="").values_list("thumbnail", flat=True)
        )
        known_files.update(
            Photo.objects.exclude(photo="").values_list("photo", flat=True)
        )
        known_files.update(
            Photo.objects.exclude(thumbnail="").values_list("thumbnail", flat=True)
        )

        # Walk all relevant subdirectories
        subdirs = [
            "site_photos",  # Photo.photo — walks all site_N subdirs via rglob
            "documents",  # Document.file
            "thumbnails/documents",  # Document.thumbnail
            "thumbnails/images",  # Photo.thumbnail
        ]
        orphaned = []
        for subdir in subdirs:
            target = media_root / subdir
            if not target.exists():
                continue
            for path in target.rglob("*"):
                if path.is_file():
                    relative = str(path.relative_to(media_root))
                    if relative not in known_files:
                        orphaned.append(path)

        if not orphaned:
            self.stdout.write("No orphaned files found.")
            return

        # Group orphaned files by top-level directory for readable output
        by_dir = {}
        for path in orphaned:
            top = str(path.relative_to(media_root)).split("/")[0]
            by_dir.setdefault(top, []).append(path)

        for subdir, paths in by_dir.items():
            self.stdout.write(f"\n{subdir}: {len(paths)} orphaned file(s)")
            for path in paths:
                if dry_run:
                    self.stdout.write(f"  Would delete: {path.name}")
                else:
                    path.unlink()
                    self.stdout.write(f"  Deleted: {path.name}")

        self.stdout.write(
            f'\n{"Would remove" if dry_run else "Removed"} '
            f"{len(orphaned)} orphaned file(s)."
        )
