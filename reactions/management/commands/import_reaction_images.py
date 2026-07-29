"""Management command to import generated reaction images into the database.

Scans static/images/reactions/ for reaction_{slug}_equation.svg files
and updates the corresponding Reaction records' structure_image_url field.
"""

from pathlib import Path
from django.core.management.base import BaseCommand
from reactions.models import Reaction


class Command(BaseCommand):
    help = "Import generated reaction SVGs into Reaction.structure_image_url."

    def handle(self, *args, **options):
        images_dir = Path("static/images/reactions")
        if not images_dir.is_dir():
            self.stderr.write(self.style.ERROR(f"Directory not found: {images_dir}"))
            return

        updated = skipped = not_found = 0

        for eq_file in sorted(images_dir.glob("reaction_*_equation.svg")):
            # Extract slug from filename: reaction_{slug}_equation.svg
            # slug may contain underscores - match from after "reaction_" to before "_equation.svg"
            name = eq_file.stem  # e.g. reaction_common_aldol_reaction_equation
            parts = name.split("_")
            if len(parts) < 3 or parts[0] != "reaction":
                self.stdout.write(f"  [SKIP] Unrecognised naming: {eq_file.name}")
                skipped += 1
                continue

            # Parts after initial "reaction" and before trailing "equation"
            # reaction_friedel_crafts_acylation_equation -> ['reaction','friedel','crafts','acylation','equation']
            # Remove leading 'reaction' and trailing 'equation'
            slug_parts = parts[1:-1]  # everything between "reaction" and "equation"
            slug = "_".join(slug_parts)

            # Try matching with underscore slugs first, then try hyphenated
            candidates = [slug, slug.replace("_", "-")]
            reaction = None
            used_slug = ""
            for candidate in candidates:
                try:
                    reaction = Reaction.objects.get(slug=candidate)
                    used_slug = candidate
                    break
                except Reaction.DoesNotExist:
                    continue

            if reaction is None:
                self.stdout.write(f"  [NOT FOUND] No reaction with slug '{slug}' (tried: {candidates})")
                not_found += 1
                continue

            url_path = f"/static/images/reactions/{eq_file.name}"
            if reaction.structure_image_url == url_path:
                self.stdout.write(f"  [SAME]  {eq_file.name} → {reaction.name_zh}")
                skipped += 1
                continue

            reaction.structure_image_url = url_path
            reaction.save(update_fields=["structure_image_url"])
            self.stdout.write(
                self.style.SUCCESS(f"  [OK]    {eq_file.name} → {reaction.name_zh} (slug={used_slug})")
            )
            updated += 1

        self.stdout.write(
            f"\nDone: {updated} updated, {skipped} skipped, {not_found} not matched"
        )
