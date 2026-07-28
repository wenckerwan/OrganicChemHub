from pathlib import Path
import re

from django.core.management.base import BaseCommand, CommandError

from reactions.models import LearningResource


SUPPORTED_EXTENSIONS = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".zip"}


def infer_category(relative_path, title):
    text = f"{relative_path} {title}"
    if "真题" in text or "考研试题" in text:
        return LearningResource.Category.PAST_EXAM
    if "答案" in text:
        return LearningResource.Category.ANSWER
    if "作业" in text or "习题" in text or "练习" in text or "专项训练" in text or "题" in text:
        return LearningResource.Category.EXERCISE
    if "课件" in text or "ppt" in text.lower():
        return LearningResource.Category.COURSEWARE
    if "讲义" in text:
        return LearningResource.Category.LECTURE
    if "大纲" in text:
        return LearningResource.Category.SYLLABUS
    if "教材" in text or "复习指南" in text:
        return LearningResource.Category.BOOK
    return LearningResource.Category.OTHER


def infer_year(text):
    match = re.search(r"(20\d{2})", text)
    if match:
        return int(match.group(1))
    return None


class Command(BaseCommand):
    help = "Index local organic chemistry learning resources as metadata."

    def add_arguments(self, parser):
        parser.add_argument("root", help="Root directory containing learning resources.")
        parser.add_argument(
            "--archive-missing",
            action="store_true",
            help="Archive existing resources under this root when files are no longer present.",
        )

    def handle(self, *args, **options):
        root = Path(options["root"]).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise CommandError(f"资料目录不存在：{root}")

        indexed_paths = set()
        created_count = 0
        updated_count = 0

        for file_path in root.rglob("*"):
            if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            relative_path = file_path.relative_to(root).as_posix()
            title = file_path.stem.strip()
            source_folder = file_path.parent.name
            local_path = str(file_path)
            has_answer = "答案" in relative_path or "答案" in title
            category = infer_category(relative_path, title)
            year = infer_year(relative_path)

            _, created = LearningResource.objects.update_or_create(
                local_path=local_path,
                defaults={
                    "title": title,
                    "category": category,
                    "year": year,
                    "file_type": file_path.suffix.lower(),
                    "size_bytes": file_path.stat().st_size,
                    "relative_path": relative_path,
                    "source_folder": source_folder,
                    "has_answer": has_answer,
                    "status": LearningResource.Status.PUBLISHED,
                },
            )
            indexed_paths.add(local_path)
            if created:
                created_count += 1
            else:
                updated_count += 1

        archived_count = 0
        if options["archive_missing"]:
            queryset = LearningResource.objects.filter(local_path__startswith=str(root)).exclude(local_path__in=indexed_paths)
            archived_count = queryset.update(status=LearningResource.Status.ARCHIVED)

        self.stdout.write(
            self.style.SUCCESS(
                f"学习资料索引完成：新增 {created_count}，更新 {updated_count}，归档 {archived_count}。"
            )
        )
