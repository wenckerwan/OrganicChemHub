"""Import reactions from a CSV file.

CSV columns (in order):
  name_zh, name_en, equation_smiles, reaction_type_slug, summary, condition, exam_tips, reference, status

Usage:
  python manage.py import_reactions_csv path/to/reactions.csv
  python manage.py import_reactions_csv path/to/reactions.csv --dry-run   # preview only, no DB writes

CSV example:
  name_zh,name_en,equation_smiles,reaction_type_slug,summary,condition,exam_tips,reference,status
  羟醛缩合,Aldol Reaction,CC=O.CC=O>>CC(O)CC=O,carbon-carbon-bond-formation,醛酮在碱作用下缩合,稀碱水溶液,考研高频,基础有机化学,published
"""

import csv
import os
import sys
from pathlib import Path

import django
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "organic_chem_hub.settings")
django.setup()

from reactions.models import Reaction, ReactionType, PublishStatus


CSV_COLUMNS = [
    "name_zh",
    "name_en",
    "equation_smiles",
    "reaction_type_slug",
    "summary",
    "condition",
    "exam_tips",
    "reference",
    "status",
]


class Command(BaseCommand):
    help = "Bulk-import reactions from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to CSV file")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview imported rows without saving",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"])
        dry_run = options["dry_run"]

        if not csv_path.is_file():
            raise CommandError(f"File not found: {csv_path}")

        created = updated = skipped = errors = 0

        # Cache reaction types by slug
        type_map = {t.slug: t for t in ReactionType.objects.all()}

        with csv_path.open(encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            # Validate columns
            missing = [c for c in CSV_COLUMNS if c not in (reader.fieldnames or [])]
            if missing:
                raise CommandError(f"Missing CSV columns: {', '.join(missing)}")

            for row_num, row in enumerate(reader, start=2):
                name_zh = (row.get("name_zh") or "").strip()
                name_en = (row.get("name_en") or "").strip()
                # Skip blank rows and comment lines
                if not name_zh and not name_en:
                    skipped += 1
                    continue

                # Auto-generate slug from name_en
                slug = slugify(name_en)
                if not slug:
                    self.stdout.write(f"  [SKIP] Row {row_num}: could not generate slug from '{name_en}'")
                    skipped += 1
                    continue

                # Ensure unique slug
                orig_slug = slug
                counter = 1
                while Reaction.objects.filter(slug=slug).exists():
                    slug = f"{orig_slug}-{counter}"
                    counter += 1

                # Resolve reaction type
                type_slug = row.get("reaction_type_slug", "").strip()
                reaction_type = type_map.get(type_slug) if type_slug else None

                # Resolve status
                status_raw = row.get("status", "").strip().lower()
                if status_raw in ("published", "已发布"):
                    status = PublishStatus.PUBLISHED
                elif status_raw in ("draft", "草稿", ""):
                    status = PublishStatus.DRAFT
                elif status_raw in ("archived", "已归档"):
                    status = PublishStatus.ARCHIVED
                else:
                    status = PublishStatus.DRAFT

                equation_smiles = row.get("equation_smiles", "").strip()

                if dry_run:
                    self.stdout.write(
                        f"  [DRY]  Row {row_num}: {name_zh} ({name_en}) → slug={slug}"
                        f" type={type_slug or '—'} smiles={'Y' if equation_smiles else 'N'}"
                    )
                    created += 1
                    continue

                try:
                    # Use slug as a unique lookup key — update if exists
                    _, is_new = Reaction.objects.update_or_create(
                        slug=slug,  # match by slug
                        defaults={
                            "name_zh": name_zh,
                            "name_en": name_en,
                            "reaction_type": reaction_type,
                            "summary": row.get("summary", "").strip(),
                            "condition": row.get("condition", "").strip(),
                            "exam_tips": row.get("exam_tips", "").strip(),
                            "reference": row.get("reference", "").strip(),
                            "status": status,
                        },
                    )
                    if is_new:
                        created += 1
                        self.stdout.write(self.style.SUCCESS(f"  [NEW]  Row {row_num}: {name_zh}"))
                    else:
                        updated += 1
                        self.stdout.write(f"  [UPD]  Row {row_num}: {name_zh} (slug '{slug}' existed, updated)")
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"  [ERR]  Row {row_num}: {e}"))
                    errors += 1

        summary = f"Done: {created} created, {updated} updated, {skipped} skipped, {errors} errors"
        if dry_run:
            self.stdout.write(self.style.WARNING(summary))
        else:
            self.stdout.write(self.style.SUCCESS(summary))
