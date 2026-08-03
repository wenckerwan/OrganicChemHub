"""Import curated exam-oriented reaction seed data into the new libraries."""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from reactions.models import (
    FunctionalGroup,
    GeneralReaction,
    GeneralReactionCategory,
    NamedReaction,
    NamedReactionCategory,
    PublishStatus,
    Tag,
)


DEFAULT_SEED_PATH = Path(__file__).resolve().parents[2] / "data" / "exam_reaction_seed.json"
REACTION_FIELDS = [
    "name_zh",
    "name_en",
    "slug",
    "aliases",
    "summary",
    "condition",
    "mechanism",
    "exam_tips",
    "scope",
    "limitations",
    "reference",
    "status",
]


class Command(BaseCommand):
    help = "Import the curated organic chemistry exam reaction seed data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            type=str,
            default=str(DEFAULT_SEED_PATH),
            help="Path to the JSON seed file.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and preview counts without writing to the database.",
        )

    def handle(self, *args, **options):
        source = Path(options["source"])
        dry_run = options["dry_run"]
        verbosity = options.get("verbosity", 1)

        if not source.is_file():
            raise CommandError(f"Seed file not found: {source}")

        try:
            data = json.loads(source.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON seed file: {exc}") from exc

        self._validate(data)
        if dry_run:
            if verbosity:
                self.stdout.write(
                    self.style.WARNING(
                        "Dry run: "
                        f"{len(data.get('named_categories', []))} named categories, "
                        f"{len(data.get('general_categories', []))} general categories, "
                        f"{len(data.get('tags', []))} tags, "
                        f"{len(data.get('functional_groups', []))} functional groups, "
                        f"{len(data.get('reactions', []))} reactions."
                    )
                )
            return

        with transaction.atomic():
            result = self._import(data)

        if verbosity:
            self.stdout.write(
                self.style.SUCCESS(
                    "Imported exam reaction seed: "
                    f"{result['named_created']} named created, {result['named_updated']} named updated, "
                    f"{result['general_created']} general created, {result['general_updated']} general updated, "
                    f"{result['categories']} categories, {result['tags']} tags, {result['functional_groups']} functional groups."
                )
            )

    def _validate(self, data):
        if not isinstance(data, dict):
            raise CommandError("Seed file root must be an object.")
        if not isinstance(data.get("reactions"), list) or not data["reactions"]:
            raise CommandError("Seed file must include a non-empty reactions list.")

        seen = set()
        for index, record in enumerate(data["reactions"], start=1):
            target = record.get("target")
            slug = record.get("slug")
            if target not in {"named", "general"}:
                raise CommandError(f"Reaction #{index} has invalid target: {target}")
            if not slug:
                raise CommandError(f"Reaction #{index} is missing slug.")
            key = (target, slug)
            if key in seen:
                raise CommandError(f"Duplicate reaction slug for {target}: {slug}")
            seen.add(key)
            for field in ("name_zh", "name_en", "summary", "condition", "exam_tips", "reference", "category_slug"):
                if not (record.get(field) or "").strip():
                    raise CommandError(f"Reaction {slug} is missing required seed field: {field}")

    def _import(self, data):
        named_categories = self._import_categories(NamedReactionCategory, data.get("named_categories", []))
        general_categories = self._import_categories(GeneralReactionCategory, data.get("general_categories", []))
        tags = self._import_tags(data.get("tags", []))
        functional_groups = self._import_functional_groups(data.get("functional_groups", []))
        result = {
            "named_created": 0,
            "named_updated": 0,
            "general_created": 0,
            "general_updated": 0,
            "categories": len(named_categories) + len(general_categories),
            "tags": len(tags),
            "functional_groups": len(functional_groups),
        }

        for record in data["reactions"]:
            target = record["target"]
            model = NamedReaction if target == "named" else GeneralReaction
            category_map = named_categories if target == "named" else general_categories
            category = category_map.get(record["category_slug"])
            if category is None:
                raise CommandError(f"Unknown category slug for {record['slug']}: {record['category_slug']}")

            defaults = {field: (record.get(field) or "") for field in REACTION_FIELDS if field != "slug"}
            defaults["status"] = record.get("status") or PublishStatus.DRAFT
            defaults["category"] = category
            obj, created = model.objects.update_or_create(slug=record["slug"], defaults=defaults)
            obj.tags.set(self._objects_for_names(tags, record.get("tags", []), "tag", record["slug"]))
            obj.functional_groups.set(
                self._objects_for_names(functional_groups, record.get("functional_groups", []), "functional group", record["slug"])
            )

            key = f"{target}_{'created' if created else 'updated'}"
            result[key] += 1

        return result

    def _import_categories(self, model, records):
        category_map = {}
        for record in records:
            obj, _ = model.objects.update_or_create(
                slug=record["slug"],
                defaults={
                    "name": record["name"],
                    "sort_order": record.get("sort_order", 0),
                    "description": record.get("description", ""),
                    "is_active": record.get("is_active", True),
                },
            )
            category_map[obj.slug] = obj
        return category_map

    def _import_tags(self, records):
        tag_map = {}
        for record in records:
            obj, _ = Tag.objects.update_or_create(
                slug=record["slug"],
                defaults={"name": record["name"], "description": record.get("description", "")},
            )
            tag_map[obj.slug] = obj
        return tag_map

    def _import_functional_groups(self, records):
        group_map = {}
        for record in records:
            obj, _ = FunctionalGroup.objects.update_or_create(
                name_zh=record["name_zh"],
                defaults={
                    "name_en": record.get("name_en", ""),
                    "smarts": record.get("smarts", ""),
                    "description": record.get("description", ""),
                },
            )
            group_map[obj.name_zh] = obj
        return group_map

    def _objects_for_names(self, object_map, names, label, slug):
        missing = [name for name in names if name not in object_map]
        if missing:
            raise CommandError(f"Unknown {label} for {slug}: {', '.join(missing)}")
        return [object_map[name] for name in names]
