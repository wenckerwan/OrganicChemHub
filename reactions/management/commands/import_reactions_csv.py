"""Deprecated legacy Reaction CSV import command."""

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Deprecated: legacy Reaction import is disabled."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", nargs="?", type=str, help="Ignored legacy CSV path")
        parser.add_argument("--dry-run", action="store_true", help="Ignored")

    def handle(self, *args, **options):
        raise CommandError(
            "import_reactions_csv writes to the deprecated Reaction table and is disabled. "
            "Use the Django Admin CSV importer at /admin/reactions/import/ for NamedReaction or GeneralReaction data."
        )
