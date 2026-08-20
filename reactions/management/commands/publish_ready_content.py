"""Publish complete draft reaction content."""
import json

from django.core.management.base import BaseCommand

from reactions.models import ContentBatch, GeneralReaction, NamedReaction
from reactions.services import audit
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
            targets.append((NamedReaction, "namedreaction", "NamedReaction", "人名反应"))
        if options["target"] in ("all", "general"):
            targets.append((GeneralReaction, "generalreaction", "GeneralReaction", "常见有机反应"))

        for model, model_name, audit_model_name, label in targets:
            if options["dry_run"]:
                count = publication_ready_queryset(model).count()
            else:
                ready_qs = publication_ready_queryset(model)
                names = [str(obj) for obj in ready_qs]
                count = publish_ready_content(model)

                if count:
                    audit.log_operation(
                        user=None,
                        action="publish",
                        model_name=model_name,
                        object_repr=f"{label} 批量发布",
                        detail=f"通过命令行发布 {count} 条。",
                    )
                    audit.record_batch(
                        kind=ContentBatch.Kind.PUBLISH,
                        operator=None,
                        summary=f"{label} 命令行批量发布",
                        objects=names,
                        detail=json.dumps({"count": count, "target": model_name}, ensure_ascii=False),
                    )
            suffix = "可发布" if options["dry_run"] else "发布"
            self.stdout.write(f"{label}{suffix} {count} 条")
