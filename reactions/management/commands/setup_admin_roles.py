from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


CONTENT_MODELS = [
    "NamedReaction",
    "GeneralReaction",
    "SyntheticRoute",
    "RouteStep",
    "LearningResource",
    "NamedReactionCategory",
    "GeneralReactionCategory",
    "ReactionType",
    "Tag",
    "FunctionalGroup",
]

OPERATIONS_MODELS = [
    "Announcement",
    "Feedback",
    "Message",
    "OpLog",
]


class Command(BaseCommand):
    help = "初始化 OrganicChemHub 后台角色：内容编辑员、运营员。"

    def handle(self, *args, **options):
        content_group = self.sync_group("内容编辑员", CONTENT_MODELS)
        operations_group = self.sync_group("运营员", OPERATIONS_MODELS)
        self.stdout.write(
            self.style.SUCCESS(
                f"已初始化角色：{content_group.name}、{operations_group.name}"
            )
        )

    def sync_group(self, group_name, model_names):
        group, _ = Group.objects.get_or_create(name=group_name)
        permissions = []
        for model_name in model_names:
            model = apps.get_model("reactions", model_name)
            content_type = ContentType.objects.get_for_model(model)
            actions = ["view", "add", "change", "delete"]
            if model_name == "OpLog":
                actions = ["view"]
            permissions.extend(
                Permission.objects.filter(
                    content_type=content_type,
                    codename__in=[f"{action}_{model._meta.model_name}" for action in actions],
                )
            )
        group.permissions.set(permissions)
        return group
