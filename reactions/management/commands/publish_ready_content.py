"""Publish complete draft reaction content."""

from django.core.management.base import BaseCommand

from reactions.models import GeneralReaction, NamedReaction
from reactions.services.publication import publication_ready_queryset, publish_ready_content


class Command(BaseCommand):
    help = "Publish complete draft NamedReaction and GeneralReaction records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--target",
            choices=["all", "named", "general"],
            default="all",
            help="Limit publishing to one reaction library.",
        )
        parser.add_argument("--dry-run", action="store_true", help="Report publishable counts without updating data.")

    def handle(self, *args, **options):
        targets = []
        if options["target"] in ("all", "named"):
            targets.append((NamedReaction, "人名反应"))
        if options["target"] in ("all", "general"):
            targets.append((GeneralReaction, "常见有机反应"))

        for model, label in targets:
            if options["dry_run"]:
                count = publication_ready_queryset(model).count()
            else:
                count = publish_ready_content(model)
            suffix = "可发布" if options["dry_run"] else "发布"
            self.stdout.write(f"{label}{suffix} {count} 条")
