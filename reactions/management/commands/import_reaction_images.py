"""Deprecated legacy Reaction image import command."""

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Deprecated: legacy Reaction image import is disabled."

    def handle(self, *args, **options):
        raise CommandError(
            "import_reaction_images updates the deprecated Reaction table and is disabled. "
            "Use the image maintenance tool at /admin/reactions/images/ for the new reaction libraries."
        )
