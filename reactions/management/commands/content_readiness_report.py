"""Content readiness report – stats and per-item CSV export."""
import csv

from django.core.management.base import BaseCommand

from reactions.services.readiness import export_rows, summary


class Command(BaseCommand):
    help = "Print content readiness stats and optionally export a per-item CSV."

    def add_arguments(self, parser):
        parser.add_argument(
            "--export",
            metavar="PATH",
            help="Export per-item readiness CSV to PATH.",
        )

    def handle(self, *args, **options):
        stats = summary()
        self.stdout.write("=== 内容就绪报告 ===")
        for model_name, data in stats.items():
            self.stdout.write(
                f"{model_name}: 总数 {data['total']}  "
                f"就绪 {data['ready']}  "
                f"缺字段 {data['missing_fields']}  "
                f"缺图片 {data['missing_images']}  "
                f"占位图 {data['placeholder_count']}"
            )

        if options["export"]:
            rows = list(export_rows())
            with open(options["export"], "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["model", "name_zh", "slug", "status", "missing", "placeholder", "ready"])
                writer.writeheader()
                writer.writerows(rows)
            self.stdout.write(f"已导出 {len(rows)} 条至 {options['export']}")

        self.stdout.write(
            f"\n汇总: 人名反应 {stats['NamedReaction']['ready']}/{stats['NamedReaction']['total']} 就绪，"
            f"常见反应 {stats['GeneralReaction']['ready']}/{stats['GeneralReaction']['total']} 就绪。"
        )