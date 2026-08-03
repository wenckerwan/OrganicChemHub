from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.contrib.messages.storage.cookie import CookieStorage
from django.test import RequestFactory
from django.test import TestCase
from django.urls import reverse
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from reactions.admin import ReactionAdmin, SyntheticRouteAdmin
from reactions.models import (
    Announcement,
    CommonReaction,
    Feedback,
    FunctionalGroup,
    GeneralReaction,
    GeneralReactionCategory,
    LearningResource,
    Message,
    NamedReaction,
    NamedReactionCategory,
    NavItem,
    PublishStatus,
    Reaction,
    ReactionImage,
    ReactionType,
    RouteStep,
    SyntheticRoute,
    Tag,
)
from reactions.services.search import build_querystring
from reactions.templatetags.search_extras import highlight_query


class ReactionModelTests(TestCase):
    def test_reaction_string_uses_chinese_name(self):
        reaction_type = ReactionType.objects.create(name="成键反应", slug="bond-forming")
        reaction = Reaction.objects.create(
            name_zh="维蒂希反应",
            name_en="Wittig Reaction",
            slug="wittig-reaction",
            reaction_type=reaction_type,
            status=Reaction.Status.PUBLISHED,
        )

        self.assertEqual(str(reaction), "维蒂希反应")

    def test_published_manager_excludes_drafts(self):
        reaction_type = ReactionType.objects.create(name="氧化反应", slug="oxidation")
        Reaction.objects.create(
            name_zh="已发布反应",
            name_en="Published Reaction",
            slug="published-reaction",
            reaction_type=reaction_type,
            status=Reaction.Status.PUBLISHED,
        )
        Reaction.objects.create(
            name_zh="草稿反应",
            name_en="Draft Reaction",
            slug="draft-reaction",
            reaction_type=reaction_type,
            status=Reaction.Status.DRAFT,
        )

        self.assertQuerySetEqual(
            Reaction.published.order_by("name_zh"),
            ["已发布反应"],
            transform=lambda reaction: reaction.name_zh,
        )

    def test_incomplete_published_reaction_fails_validation(self):
        reaction = Reaction(
            name_zh="不完整反应",
            name_en="Incomplete Reaction",
            slug="incomplete-reaction",
            status=Reaction.Status.PUBLISHED,
        )

        with self.assertRaises(ValidationError) as context:
            reaction.full_clean()

        self.assertIn("summary", context.exception.message_dict)
        self.assertIn("condition", context.exception.message_dict)
        self.assertIn("reference", context.exception.message_dict)

    def test_reaction_content_completeness_counts_required_fields(self):
        reaction = Reaction(
            name_zh="维蒂希反应",
            name_en="Wittig Reaction",
            slug="wittig-reaction",
            summary="羰基到烯烃。",
            condition="膦叶立德。",
            reference="教材。",
        )

        self.assertEqual(reaction.get_publication_missing_fields(), [])
        self.assertEqual(reaction.content_completeness(), "3/3")

    def test_reaction_structure_image_source_prefers_uploaded_file_then_url(self):
        reaction = Reaction(
            name_zh="维蒂希反应",
            name_en="Wittig Reaction",
            slug="wittig-reaction",
            structure_image_url="/static/img/reactions/wittig.png",
        )

        self.assertEqual(reaction.get_structure_image_src(), "/static/img/reactions/wittig.png")

        reaction.structure_image = "reaction_structures/uploaded-wittig.png"

        self.assertEqual(reaction.get_structure_image_src(), "/media/reaction_structures/uploaded-wittig.png")

    def test_get_equation_img_uses_equation_img_first(self):
        reaction = Reaction(
            name_zh="测试",
            name_en="Test Reaction",
            slug="test-eq-priority",
            structure_image_url="/static/images/legacy.svg",
        )

        self.assertEqual(reaction.get_equation_img_src(), "/static/images/legacy.svg")

        # When equation_img is uploaded, it takes priority
        reaction.equation_img = "reaction_images/reaction_test_eq_priority_equation.svg"
        self.assertTrue(reaction.get_equation_img_src().endswith("reaction_images/reaction_test_eq_priority_equation.svg"))

    def test_reaction_new_image_getters_return_empty_by_default(self):
        reaction = Reaction(
            name_zh="测试",
            name_en="Test Reaction",
            slug="test-reaction",
        )

        self.assertEqual(reaction.get_equation_img_src(), "")
        self.assertEqual(reaction.get_mechanism_img_src(), "")
        self.assertEqual(reaction.get_thumbnail_img_src(), "")

    def test_get_equation_img_falls_back_to_structure_image_url(self):
        reaction = Reaction(
            name_zh="测试",
            name_en="Test Reaction",
            slug="test-fallback",
            structure_image_url="/static/images/legacy.svg",
        )

        self.assertEqual(reaction.get_equation_img_src(), "/static/images/legacy.svg")


class SyntheticRouteModelTests(TestCase):
    def test_route_steps_order_by_step_number(self):
        route = SyntheticRoute.objects.create(
            target_product="苯乙酮",
            slug="acetophenone",
            status=SyntheticRoute.Status.PUBLISHED,
        )
        RouteStep.objects.create(route=route, step_number=2, title="氧化")
        RouteStep.objects.create(route=route, step_number=1, title="烷基化")

        self.assertEqual([step.title for step in route.steps.all()], ["烷基化", "氧化"])

    def test_incomplete_published_route_without_steps_fails_validation(self):
        route = SyntheticRoute.objects.create(
            target_product="苯乙酮",
            slug="acetophenone-route-draft",
            summary="从苯出发。",
        )
        route.status = SyntheticRoute.Status.PUBLISHED

        with self.assertRaises(ValidationError) as context:
            route.full_clean()

        self.assertIn("steps", context.exception.message_dict)

    def test_route_content_completeness_includes_steps(self):
        route = SyntheticRoute.objects.create(
            target_product="苯乙酮",
            slug="acetophenone-complete-route",
            summary="从苯出发。",
        )
        RouteStep.objects.create(route=route, step_number=1, title="酰基化")

        self.assertEqual(route.get_publication_missing_fields(), [])
        self.assertEqual(route.content_completeness(), "3/3")


class AdminRegistrationTests(TestCase):
    def test_core_models_are_registered_in_admin(self):
        self.assertNotIn(Reaction, admin.site._registry)
        self.assertNotIn(CommonReaction, admin.site._registry)
        self.assertNotIn(ReactionType, admin.site._registry)
        self.assertIn(Tag, admin.site._registry)
        self.assertIn(SyntheticRoute, admin.site._registry)


class AdminMaintenanceTests(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.factory = RequestFactory()

    def _request(self):
        request = self.factory.post("/admin/")
        request._messages = CookieStorage(request)
        return request

    def test_reaction_admin_publish_selected_skips_incomplete_reactions(self):
        complete = Reaction.objects.create(
            name_zh="完整反应",
            name_en="Complete Reaction",
            slug="complete-reaction",
            summary="摘要。",
            condition="条件。",
            reference="来源。",
        )
        incomplete = Reaction.objects.create(
            name_zh="不完整反应",
            name_en="Incomplete Reaction",
            slug="incomplete-reaction-admin",
        )
        model_admin = ReactionAdmin(Reaction, self.site)

        model_admin.publish_selected(self._request(), Reaction.objects.filter(pk__in=[complete.pk, incomplete.pk]))

        complete.refresh_from_db()
        incomplete.refresh_from_db()
        self.assertEqual(complete.status, Reaction.Status.PUBLISHED)
        self.assertEqual(incomplete.status, Reaction.Status.DRAFT)

    def test_reaction_admin_archive_selected_archives_reactions(self):
        reaction = Reaction.objects.create(
            name_zh="已发布反应",
            name_en="Published Reaction",
            slug="published-reaction-admin",
            summary="摘要。",
            condition="条件。",
            reference="来源。",
            status=Reaction.Status.PUBLISHED,
        )
        model_admin = ReactionAdmin(Reaction, self.site)

        model_admin.archive_selected(self._request(), Reaction.objects.filter(pk=reaction.pk))

        reaction.refresh_from_db()
        self.assertEqual(reaction.status, Reaction.Status.ARCHIVED)

    def test_route_admin_publish_selected_skips_routes_without_steps(self):
        complete = SyntheticRoute.objects.create(
            target_product="完整路线",
            slug="complete-route",
            summary="摘要。",
        )
        RouteStep.objects.create(route=complete, step_number=1, title="第一步")
        incomplete = SyntheticRoute.objects.create(
            target_product="不完整路线",
            slug="incomplete-route-admin",
            summary="摘要。",
        )
        model_admin = SyntheticRouteAdmin(SyntheticRoute, self.site)

        model_admin.publish_selected(self._request(), SyntheticRoute.objects.filter(pk__in=[complete.pk, incomplete.pk]))

        complete.refresh_from_db()
        incomplete.refresh_from_db()
        self.assertEqual(complete.status, SyntheticRoute.Status.PUBLISHED)
        self.assertEqual(incomplete.status, SyntheticRoute.Status.DRAFT)

    def test_route_admin_step_count_column_returns_step_total(self):
        route = SyntheticRoute.objects.create(
            target_product="苯乙酮",
            slug="acetophenone-admin-column",
            summary="摘要。",
        )
        RouteStep.objects.create(route=route, step_number=1, title="第一步")
        RouteStep.objects.create(route=route, step_number=2, title="第二步")
        model_admin = SyntheticRouteAdmin(SyntheticRoute, self.site)

        self.assertEqual(model_admin.step_count(route), 2)


class PublicViewTests(TestCase):
    def setUp(self):
        self.reaction_type = ReactionType.objects.create(name="碳链增长", slug="chain-extension")
        self.other_reaction_type = ReactionType.objects.create(name="氧化反应", slug="oxidation")
        self.tag = Tag.objects.create(name="考研高频", slug="exam-high-frequency")
        self.other_tag = Tag.objects.create(name="普通反应", slug="normal-reaction")
        self.functional_group = FunctionalGroup.objects.create(name_zh="羰基", name_en="Carbonyl", smarts="[CX3]=[OX1]")
        self.other_functional_group = FunctionalGroup.objects.create(name_zh="芳香环", name_en="Arene", smarts="a")
        self.reaction = Reaction.objects.create(
            name_zh="维蒂希反应",
            name_en="Wittig Reaction",
            aliases="Wittig olefination",
            slug="wittig-reaction",
            reaction_type=self.reaction_type,
            condition="膦叶立德与醛酮反应",
            summary="醛酮转化为烯烃的经典反应。",
            structure_image_url="/static/img/reactions/lecture_001.png",
            structure_image_caption="讲义结构式示例",
            status=Reaction.Status.PUBLISHED,
        )
        self.reaction.tags.add(self.tag)
        self.reaction.functional_groups.add(self.functional_group)
        self.named_category = NamedReactionCategory.objects.create(name="碳链增长", slug="chain-extension-new")
        self.other_named_category = NamedReactionCategory.objects.create(name="氧化反应", slug="oxidation-new")
        self.named_reaction = NamedReaction.objects.create(
            name_zh=self.reaction.name_zh,
            name_en=self.reaction.name_en,
            aliases=self.reaction.aliases,
            slug=self.reaction.slug,
            category=self.named_category,
            condition=self.reaction.condition,
            summary=self.reaction.summary,
            exam_tips="考点",
            reference="来源",
            equation_img="named_reactions/lecture_001.png",
            thumbnail_img="named_reactions/lecture_001_thumb.png",
            status=PublishStatus.PUBLISHED,
        )
        self.named_reaction.tags.add(self.tag)
        self.named_reaction.functional_groups.add(self.functional_group)
        self.other_reaction = Reaction.objects.create(
            name_zh="普通氧化反应",
            name_en="Oxidation Example",
            aliases="",
            slug="oxidation-example",
            reaction_type=self.other_reaction_type,
            condition="氧化剂",
            summary="芳香环相关示例。",
            reference="教材。",
            status=Reaction.Status.PUBLISHED,
        )
        self.other_reaction.tags.add(self.other_tag)
        self.other_reaction.functional_groups.add(self.other_functional_group)
        self.other_named_reaction = NamedReaction.objects.create(
            name_zh=self.other_reaction.name_zh,
            name_en=self.other_reaction.name_en,
            aliases=self.other_reaction.aliases,
            slug=self.other_reaction.slug,
            category=self.other_named_category,
            condition=self.other_reaction.condition,
            summary=self.other_reaction.summary,
            exam_tips="考点",
            reference="来源",
            equation_img="named_reactions/oxidation_equation.png",
            thumbnail_img="named_reactions/oxidation_thumb.png",
            status=PublishStatus.PUBLISHED,
        )
        self.other_named_reaction.tags.add(self.other_tag)
        self.other_named_reaction.functional_groups.add(self.other_functional_group)
        Reaction.objects.create(
            name_zh="未发布反应",
            name_en="Hidden Reaction",
            slug="hidden-reaction",
            reaction_type=self.reaction_type,
            status=Reaction.Status.DRAFT,
        )
        NamedReaction.objects.create(
            name_zh="未发布反应",
            name_en="Hidden Reaction",
            slug="hidden-reaction",
            category=self.named_category,
            status=PublishStatus.DRAFT,
        )
        self.route = SyntheticRoute.objects.create(
            target_product="苯乙酮",
            target_structure_image_url="/static/img/reactions/lecture_002.png",
            slug="acetophenone",
            summary="从苯出发的基础路线。",
            status=SyntheticRoute.Status.PUBLISHED,
        )
        self.route.related_reactions.add(self.reaction)
        self.route.related_named_reactions.add(self.named_reaction)
        RouteStep.objects.create(
            route=self.route,
            step_number=1,
            title="Friedel-Crafts 酰基化",
            reagents="乙酰氯，AlCl3",
            condition="无水条件",
            product_structure_image_url="/static/img/reactions/lecture_003.png",
        )
        self.long_route = SyntheticRoute.objects.create(
            target_product="乙醇",
            slug="ethanol",
            summary="两步路线。",
            difficulty=SyntheticRoute.Difficulty.ADVANCED,
            status=SyntheticRoute.Status.PUBLISHED,
        )
        RouteStep.objects.create(route=self.long_route, step_number=1, title="第一步")
        RouteStep.objects.create(route=self.long_route, step_number=2, title="第二步")

    def test_homepage_loads(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "OrganicChemHub")
        self.assertContains(response, "维蒂希反应")

    def test_homepage_admin_maintenance_button_is_staff_only(self):
        anonymous_response = self.client.get(reverse("home"))

        self.assertNotContains(anonymous_response, "进入后台维护")

        normal_user = User.objects.create_user("normal-user", "normal@example.com", "password")
        self.client.force_login(normal_user)
        normal_response = self.client.get(reverse("home"))

        self.assertNotContains(normal_response, "进入后台维护")

        self.client.logout()
        staff_user = User.objects.create_superuser("staff-user", "staff@example.com", "password")
        self.client.force_login(staff_user)
        staff_response = self.client.get(reverse("home"))

        self.assertContains(staff_response, "进入后台维护")

    def test_reaction_list_searches_name_and_condition(self):
        response = self.client.get(reverse("reaction_list"), {"q": "膦叶立德"})

        self.assertContains(response, "维蒂希反应")
        self.assertNotContains(response, "未发布反应")

    def test_reaction_list_uses_reference_browser_layout(self):
        response = self.client.get(reverse("reaction_list"))

        self.assertContains(response, "reaction-browser")
        self.assertContains(response, "reaction-browser--named")
        self.assertContains(response, 'class="reaction-browser__sidebar"')
        self.assertContains(response, 'class="reaction-browser__content"')
        self.assertContains(response, "人名反应库")
        self.assertContains(response, "收录以发现者或经典命名方式流传的人名反应")

    def test_reaction_list_filters_by_functional_group(self):
        response = self.client.get(reverse("reaction_list"), {"functional_group": self.functional_group.pk})

        self.assertContains(response, "维蒂希反应")
        self.assertNotContains(response, "普通氧化反应")

    def test_reaction_list_exam_quick_filter_uses_exam_tags(self):
        response = self.client.get(reverse("reaction_list"), {"exam": "1"})

        self.assertContains(response, "维蒂希反应")
        self.assertNotContains(response, "普通氧化反应")

    def test_reaction_list_sorts_by_type(self):
        response = self.client.get(reverse("reaction_list"), {"sort": "type"})

        names = [reaction.name_zh for reaction in response.context["reactions"]]
        self.assertEqual(names, ["维蒂希反应", "普通氧化反应"])

    def test_reaction_list_highlights_query(self):
        response = self.client.get(reverse("reaction_list"), {"q": "维蒂希"})

        self.assertContains(response, '<mark class="search-highlight">维蒂希</mark>', html=True)

    def test_reaction_list_empty_result_shows_recommendations(self):
        response = self.client.get(reverse("reaction_list"), {"q": "不存在的反应"})

        self.assertContains(response, "推荐查看")
        self.assertContains(response, "维蒂希反应")

    def test_reaction_detail_shows_published_reaction(self):
        response = self.client.get(reverse("reaction_detail", kwargs={"slug": "wittig-reaction"}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wittig Reaction")
        self.assertContains(response, "醛酮转化为烯烃")

    def test_reaction_detail_uses_structure_image_instead_of_online_renderer(self):
        response = self.client.get(reverse("reaction_detail", kwargs={"slug": "wittig-reaction"}))

        self.assertContains(response, 'class="structure-image-frame"')
        self.assertContains(response, 'src="/media/named_reactions/lecture_001.png"')

    def test_reaction_detail_shows_fallback_when_no_image(self):
        self.named_reaction.equation_img = ""
        self.named_reaction.thumbnail_img = ""
        self.named_reaction.save(update_fields=["equation_img", "thumbnail_img"])

        response = self.client.get(reverse("reaction_detail", kwargs={"slug": "wittig-reaction"}))

        self.assertNotContains(response, 'src="/media/named_reactions/lecture_001.png"')

    def test_draft_reaction_returns_404(self):
        response = self.client.get(reverse("reaction_detail", kwargs={"slug": "hidden-reaction"}))

        self.assertEqual(response.status_code, 404)

    def test_route_list_searches_target_product(self):
        response = self.client.get(reverse("route_list"), {"q": "苯乙酮"})

        self.assertContains(response, "苯乙酮")

    def test_route_list_sorts_by_step_count(self):
        response = self.client.get(reverse("route_list"), {"sort": "steps"})

        route_names = [route.target_product for route in response.context["routes"]]
        self.assertEqual(route_names, ["乙醇", "苯乙酮"])

    def test_route_list_empty_result_shows_recommendations(self):
        response = self.client.get(reverse("route_list"), {"q": "不存在的路线"})

        self.assertContains(response, "推荐查看")
        self.assertContains(response, "苯乙酮")

    def test_route_detail_shows_steps_and_related_reactions(self):
        response = self.client.get(reverse("route_detail", kwargs={"slug": "acetophenone"}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Friedel-Crafts 酰基化")
        self.assertContains(response, "维蒂希反应")

    def test_common_reaction_legacy_url_redirects_to_general_reactions(self):
        response = self.client.get(reverse("common_reaction_list"))

        self.assertRedirects(response, reverse("general_reaction_list"), status_code=302, target_status_code=200)

    def test_old_reaction_without_named_counterpart_is_hidden_from_frontend(self):
        Reaction.objects.create(
            name_zh="旧版反应",
            name_en="Legacy Only Reaction",
            slug="legacy-only-reaction",
            summary="旧版摘要",
            condition="旧版条件",
            reference="旧版来源",
            status=Reaction.Status.PUBLISHED,
        )

        list_response = self.client.get(reverse("reaction_list"), {"q": "Legacy Only"})
        detail_response = self.client.get(reverse("reaction_detail", kwargs={"slug": "legacy-only-reaction"}))

        self.assertNotContains(list_response, "Legacy Only Reaction")
        self.assertEqual(detail_response.status_code, 404)

    def test_route_detail_uses_structure_images_instead_of_online_renderer(self):
        response = self.client.get(reverse("route_detail", kwargs={"slug": "acetophenone"}))

        self.assertContains(response, 'src="/static/img/reactions/lecture_002.png"')
        self.assertContains(response, 'src="/static/img/reactions/lecture_003.png"')

    def test_deploy_guide_loads(self):
        response = self.client.get(reverse("deploy_guide"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "首次部署")
        self.assertContains(response, "宝塔面板")


class CommonReactionFixtureTests(TestCase):
    def test_common_reactions_fixture_loads_searchable_published_reactions(self):
        call_command("loaddata", "common_reactions", verbosity=0)

        self.assertGreaterEqual(Reaction.published.count(), 10)
        response = self.client.get(reverse("reaction_list"), {"q": "Diels"})
        self.assertNotContains(response, "Diels-Alder")

    def test_exam_reactions_fixture_adds_common_postgraduate_reactions(self):
        call_command("loaddata", "common_reactions", "exam_reactions", verbosity=0)

        self.assertGreaterEqual(Reaction.published.count(), 40)
        response = self.client.get(reverse("reaction_list"), {"q": "Sandmeyer"})
        self.assertNotContains(response, "Sandmeyer Reaction")


class LegacyCommandDeprecationTests(TestCase):
    def test_old_reaction_csv_import_command_is_disabled(self):
        with TemporaryDirectory() as directory:
            csv_path = Path(directory) / "reactions.csv"
            csv_path.write_text("name_zh,name_en\n旧版,Legacy\n", encoding="utf-8")

            with self.assertRaises(CommandError):
                call_command("import_reactions_csv", str(csv_path), verbosity=0)

    def test_old_reaction_image_import_command_is_disabled(self):
        with self.assertRaises(CommandError):
            call_command("import_reaction_images", verbosity=0)


class ExamReactionSeedImportTests(TestCase):
    def test_import_exam_reaction_seed_creates_new_reaction_libraries(self):
        call_command("import_exam_reaction_seed", verbosity=0)

        self.assertEqual(NamedReaction.objects.count(), 40)
        self.assertEqual(GeneralReaction.objects.count(), 42)
        self.assertTrue(NamedReaction.objects.filter(slug="diels-alder-reaction").exists())
        self.assertTrue(NamedReaction.objects.filter(slug="williamson-ether-synthesis").exists())
        self.assertTrue(GeneralReaction.objects.filter(slug="epoxide-acidic-ring-opening").exists())
        self.assertTrue(GeneralReaction.objects.filter(slug="fehling-test").exists())
        self.assertTrue(Tag.objects.filter(slug="exam-completion").exists())
        self.assertTrue(FunctionalGroup.objects.filter(name_zh="环氧").exists())

    def test_import_exam_reaction_seed_is_idempotent(self):
        call_command("import_exam_reaction_seed", verbosity=0)
        call_command("import_exam_reaction_seed", verbosity=0)

        self.assertEqual(NamedReaction.objects.count(), 40)
        self.assertEqual(GeneralReaction.objects.count(), 42)


class LearningResourceTests(TestCase):
    def test_learning_resource_string_uses_title(self):
        resource = LearningResource.objects.create(
            title="2019 有机化学真题",
            category=LearningResource.Category.PAST_EXAM,
            file_type=".pdf",
            size_bytes=1024,
            local_path="F:\\2027考研资料\\有机化学\\有机真题\\2019.pdf",
            relative_path="有机真题/2019.pdf",
            status=LearningResource.Status.PUBLISHED,
        )

        self.assertEqual(str(resource), "2019 有机化学真题")

    def test_learning_resource_list_searches_title_and_filters_category(self):
        LearningResource.objects.create(
            title="2019 有机化学真题",
            category=LearningResource.Category.PAST_EXAM,
            file_type=".pdf",
            size_bytes=1024,
            local_path="F:\\2027考研资料\\有机化学\\有机真题\\2019.pdf",
            relative_path="有机真题/2019.pdf",
            status=LearningResource.Status.PUBLISHED,
        )
        LearningResource.objects.create(
            title="醛酮章节课件",
            category=LearningResource.Category.COURSEWARE,
            file_type=".pptx",
            size_bytes=2048,
            local_path="F:\\2027考研资料\\有机化学\\课件\\醛酮.pptx",
            relative_path="课件/醛酮.pptx",
            status=LearningResource.Status.PUBLISHED,
        )

        response = self.client.get(
            reverse("learning_resource_list"),
            {"q": "2019", "category": LearningResource.Category.PAST_EXAM},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2019 有机化学真题")
        self.assertNotContains(response, "醛酮章节课件")

    def test_learning_resource_list_loads_without_filters(self):
        LearningResource.objects.create(
            title="2019 有机化学真题",
            category=LearningResource.Category.PAST_EXAM,
            file_type=".pdf",
            size_bytes=1024,
            local_path="F:\\2027考研资料\\有机化学\\有机真题\\2019-no-filter.pdf",
            relative_path="有机真题/2019-no-filter.pdf",
            status=LearningResource.Status.PUBLISHED,
        )

        response = self.client.get(reverse("learning_resource_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2019 有机化学真题")

    def test_learning_resource_list_sorts_by_year(self):
        LearningResource.objects.create(
            title="2018 有机化学真题",
            category=LearningResource.Category.PAST_EXAM,
            year=2018,
            file_type=".pdf",
            size_bytes=1024,
            local_path="F:\\2027考研资料\\有机化学\\有机真题\\2018.pdf",
            relative_path="有机真题/2018.pdf",
            status=LearningResource.Status.PUBLISHED,
        )
        LearningResource.objects.create(
            title="2020 有机化学真题",
            category=LearningResource.Category.PAST_EXAM,
            year=2020,
            file_type=".pdf",
            size_bytes=1024,
            local_path="F:\\2027考研资料\\有机化学\\有机真题\\2020.pdf",
            relative_path="有机真题/2020.pdf",
            status=LearningResource.Status.PUBLISHED,
        )

        response = self.client.get(reverse("learning_resource_list"), {"sort": "year"})

        titles = [resource.title for resource in response.context["resources"]]
        self.assertEqual(titles, ["2020 有机化学真题", "2018 有机化学真题"])

    def test_learning_resource_empty_result_shows_recommendations(self):
        LearningResource.objects.create(
            title="2019 有机化学真题",
            category=LearningResource.Category.PAST_EXAM,
            year=2019,
            file_type=".pdf",
            size_bytes=1024,
            local_path="F:\\2027考研资料\\有机化学\\有机真题\\2019-empty.pdf",
            relative_path="有机真题/2019-empty.pdf",
            status=LearningResource.Status.PUBLISHED,
        )

        response = self.client.get(reverse("learning_resource_list"), {"q": "不存在的资料"})

        self.assertContains(response, "推荐查看")
        self.assertContains(response, "2019 有机化学真题")

    def test_index_learning_resources_command_indexes_supported_files(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            past_exam_dir = root / "有机真题"
            exercise_dir = root / "作业题答案"
            past_exam_dir.mkdir()
            exercise_dir.mkdir()
            (past_exam_dir / "2019.pdf").write_bytes(b"pdf")
            (exercise_dir / "第11章 作业题 - 答案.docx").write_bytes(b"docx")
            (root / "ignore.tmp").write_text("ignore", encoding="utf-8")

            call_command("index_learning_resources", str(root), verbosity=0)

        self.assertEqual(LearningResource.objects.count(), 2)
        exam = LearningResource.objects.get(title__contains="2019")
        answer = LearningResource.objects.get(title__contains="答案")
        self.assertEqual(exam.category, LearningResource.Category.PAST_EXAM)
        self.assertTrue(answer.has_answer)


class SearchUtilityTests(TestCase):
    def test_build_querystring_preserves_filters_and_replaces_page(self):
        querystring = build_querystring({"q": "Wittig", "tag": "exam", "page": "2"}, page=3)

        self.assertIn("q=Wittig", querystring)
        self.assertIn("tag=exam", querystring)
        self.assertIn("page=3", querystring)
        self.assertNotIn("page=2", querystring)

    def test_highlight_query_marks_matches_and_escapes_html(self):
        highlighted = highlight_query("<b>Wittig</b> Reaction", "Wittig")

        self.assertIn("&lt;b&gt;", highlighted)
        self.assertIn('<mark class="search-highlight">Wittig</mark>', highlighted)

class AdminRedesignModelTests(TestCase):
    def test_named_reaction_requires_core_fields_and_images_for_publish(self):
        reaction = NamedReaction(
            name_zh="维蒂希反应",
            name_en="Wittig Reaction",
            slug="wittig-reaction",
            status=PublishStatus.PUBLISHED,
        )

        with self.assertRaises(ValidationError) as context:
            reaction.full_clean()

        self.assertIn("summary", context.exception.message_dict)
        self.assertIn("condition", context.exception.message_dict)
        self.assertIn("exam_tips", context.exception.message_dict)
        self.assertIn("reference", context.exception.message_dict)
        self.assertIn("equation_img", context.exception.message_dict)
        self.assertIn("thumbnail_img", context.exception.message_dict)
        self.assertNotIn("mechanism_img", context.exception.message_dict)

    def test_general_reaction_has_separate_category_and_optional_mechanism_image(self):
        category = GeneralReactionCategory.objects.create(name="加成反应", slug="addition")
        reaction = GeneralReaction(
            name_zh="亲电加成",
            name_en="Electrophilic Addition",
            slug="electrophilic-addition",
            category=category,
            summary="烯烃与亲电试剂加成。",
            condition="酸性或卤素条件。",
            exam_tips="注意马氏规则。",
            reference="教材。",
            equation_img="general_reactions/general_electrophilic_addition_equation.svg",
            thumbnail_img="general_reactions/general_electrophilic_addition_thumbnail.svg",
            status=PublishStatus.PUBLISHED,
        )

        reaction.full_clean()
        self.assertEqual(reaction.get_publication_missing_fields(), [])
        self.assertEqual(reaction.content_completeness(), "6/6")
        self.assertEqual(reaction.missing_fields_display(), "完整")

class AdminRedesignRegistrationTests(TestCase):
    def test_new_content_models_are_registered(self):
        self.assertIn(NamedReaction, admin.site._registry)
        self.assertIn(GeneralReaction, admin.site._registry)
        self.assertIn(NamedReactionCategory, admin.site._registry)
        self.assertIn(GeneralReactionCategory, admin.site._registry)

    def test_mechanism_image_not_required_for_admin_publish(self):
        category = NamedReactionCategory.objects.create(name="重排反应", slug="rearrangement")
        reaction = NamedReaction.objects.create(
            name_zh="测试反应",
            name_en="Test Reaction",
            slug="test-reaction-admin",
            category=category,
            summary="摘要",
            condition="条件",
            exam_tips="考点",
            reference="来源",
            equation_img="named_reactions/reaction_test_reaction_admin_equation.svg",
            thumbnail_img="named_reactions/reaction_test_reaction_admin_thumbnail.svg",
        )
        model_admin = admin.site._registry[NamedReaction]
        request = RequestFactory().post("/admin/")
        request._messages = CookieStorage(request)

        model_admin.publish_selected(request, NamedReaction.objects.filter(pk=reaction.pk))

        reaction.refresh_from_db()
        self.assertEqual(reaction.status, PublishStatus.PUBLISHED)

class AdminToolPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin", "admin@example.com", "password")
        self.client.force_login(self.user)

    def test_admin_index_shows_tool_links(self):
        response = self.client.get("/admin/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "内容质量仪表盘")
        self.assertContains(response, 'href="/admin/reactions/dashboard/"')
        self.assertContains(response, 'href="/admin/reactions/import/"')
        self.assertContains(response, 'href="/admin/reactions/images/"')
        self.assertContains(response, 'href="/admin/operations/messages/send/"')
        self.assertContains(response, 'href="/admin/operations/messages/cleanup/"')
        self.assertContains(response, 'href="/admin/resources/import-or-upload/"')
        self.assertContains(response, "och-admin-tool-icon-wrap")
        self.assertContains(response, "och-admin-tool-arrow")
        self.assertContains(response, "och-admin-tool-link--primary")
        self.assertContains(response, "och-admin-app-grid")
        self.assertContains(response, "och-admin-model-card")
        self.assertLess(
            response.content.index(b"och-admin-tools"),
            response.content.index(b"och-admin-app-grid"),
        )

    def test_admin_pages_use_unified_skin(self):
        pages = [
            "/admin/",
            "/admin/reactions/namedreaction/",
            "/admin/reactions/namedreaction/add/",
            "/admin/reactions/dashboard/",
            "/admin/reactions/import/",
            "/admin/reactions/images/",
            "/admin/operations/messages/send/",
            "/admin/operations/messages/cleanup/",
            "/admin/resources/import-or-upload/",
        ]

        for url in pages:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "och-admin")

        self.assertContains(self.client.get("/admin/reactions/dashboard/"), "och-admin-stat-grid")
        self.assertContains(self.client.get("/admin/reactions/import/"), "och-admin-form-card")
        self.assertContains(self.client.get("/admin/reactions/images/"), "och-admin-list-card")

    def test_dashboard_loads(self):
        response = self.client.get("/admin/reactions/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "内容质量仪表盘")

    def test_import_page_loads(self):
        response = self.client.get("/admin/reactions/import/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CSV 导入")

    def test_image_page_loads(self):
        response = self.client.get("/admin/reactions/images/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "图片维护")

    def test_message_broadcast_page_loads(self):
        response = self.client.get("/admin/operations/messages/send/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "站内消息群发")

    def test_message_cleanup_page_loads(self):
        response = self.client.get("/admin/operations/messages/cleanup/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "消息清理")

    def test_resource_tool_page_loads(self):
        response = self.client.get("/admin/resources/import-or-upload/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "学习资料上传和登记")
    def test_reaction_import_creates_named_reaction(self):
        csv_file = SimpleUploadedFile(
            "reactions.csv",
            (
                "name_zh,name_en,slug,summary,condition,exam_tips,reference,status\n"
                "CSV反应,CSV Reaction,csv-reaction,摘要,条件,考点,来源,draft\n"
            ).encode("utf-8-sig"),
            content_type="text/csv",
        )

        response = self.client.post(
            "/admin/reactions/import/",
            {"target": "named", "mode": "create", "csv_file": csv_file},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "新增 1")
        self.assertTrue(NamedReaction.objects.filter(slug="csv-reaction").exists())

    def test_dashboard_reports_missing_required_images(self):
        NamedReaction.objects.create(
            name_zh="缺图反应",
            name_en="Missing Image Reaction",
            slug="missing-image-reaction",
            summary="摘要",
            condition="条件",
            exam_tips="考点",
            reference="来源",
        )

        response = self.client.get("/admin/reactions/dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "缺方程式图")
        self.assertContains(response, "缺缩略图")
        self.assertContains(response, 'id="named-missing-equation">1')
        self.assertContains(response, 'id="named-missing-thumbnail">1')

class FrontendRedesignTests(TestCase):
    def setUp(self):
        self.named_category = NamedReactionCategory.objects.create(name="偶联反应", slug="coupling")
        self.general_category = GeneralReactionCategory.objects.create(name="加成反应", slug="addition-general")
        self.named = NamedReaction.objects.create(
            name_zh="新维蒂希反应",
            name_en="New Wittig Reaction",
            slug="new-wittig-reaction",
            category=self.named_category,
            summary="新模型摘要",
            condition="新模型条件",
            exam_tips="新模型考点",
            reference="新模型来源",
            equation_img="named_reactions/new_wittig_equation.svg",
            thumbnail_img="named_reactions/new_wittig_thumbnail.svg",
            status=PublishStatus.PUBLISHED,
        )
        NamedReaction.objects.create(
            name_zh="隐藏人名反应",
            name_en="Hidden Named Reaction",
            slug="hidden-named-reaction",
            category=self.named_category,
            status=PublishStatus.DRAFT,
        )
        self.general = GeneralReaction.objects.create(
            name_zh="亲电加成",
            name_en="Electrophilic Addition",
            slug="electrophilic-addition-new",
            category=self.general_category,
            summary="常见反应摘要",
            condition="常见反应条件",
            exam_tips="常见反应考点",
            reference="常见反应来源",
            equation_img="general_reactions/electrophilic_addition_equation.svg",
            thumbnail_img="general_reactions/electrophilic_addition_thumbnail.svg",
            status=PublishStatus.PUBLISHED,
        )
        GeneralReaction.objects.create(
            name_zh="隐藏常见反应",
            name_en="Hidden General Reaction",
            slug="hidden-general-reaction",
            category=self.general_category,
            status=PublishStatus.ARCHIVED,
        )

    def test_reaction_list_uses_published_named_reactions(self):
        response = self.client.get(reverse("reaction_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "新维蒂希反应")
        self.assertNotContains(response, "隐藏人名反应")

    def test_reaction_detail_uses_published_named_reaction(self):
        response = self.client.get(reverse("reaction_detail", kwargs={"slug": "new-wittig-reaction"}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "New Wittig Reaction")
        self.assertContains(response, "新模型摘要")

    def test_general_reaction_list_uses_published_general_reactions(self):
        response = self.client.get(reverse("general_reaction_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "亲电加成")
        self.assertNotContains(response, "隐藏常见反应")

    def test_general_reaction_detail_uses_published_general_reaction(self):
        response = self.client.get(reverse("general_reaction_detail", kwargs={"slug": "electrophilic-addition-new"}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Electrophilic Addition")
        self.assertContains(response, "常见反应摘要")


class FrontendReactionLibrarySeparationTests(TestCase):
    def setUp(self):
        named_category = NamedReactionCategory.objects.create(name="Named Category", slug="named-category")
        general_category = GeneralReactionCategory.objects.create(name="General Category", slug="general-category")
        tag = Tag.objects.create(name="考研高频", slug="exam-high-frequency")
        self.named = NamedReaction.objects.create(
            name_zh="Named Only Reaction",
            name_en="Named Only Reaction",
            slug="named-only-reaction",
            category=named_category,
            summary="Named summary",
            condition="Named condition",
            exam_tips="Named tips",
            reference="Named source",
            equation_img="named_reactions/named_only_equation.svg",
            thumbnail_img="named_reactions/named_only_thumbnail.svg",
            status=PublishStatus.PUBLISHED,
        )
        self.named.tags.add(tag)
        self.general = GeneralReaction.objects.create(
            name_zh="General Only Reaction",
            name_en="General Only Reaction",
            slug="general-only-reaction",
            category=general_category,
            summary="General summary",
            condition="General condition",
            exam_tips="General tips",
            reference="General source",
            equation_img="general_reactions/general_only_equation.svg",
            thumbnail_img="general_reactions/general_only_thumbnail.svg",
            status=PublishStatus.PUBLISHED,
        )
        self.general.tags.add(tag)

    def test_named_and_general_lists_do_not_cross_display(self):
        named_response = self.client.get(reverse("reaction_list"))
        general_response = self.client.get(reverse("general_reaction_list"))

        self.assertContains(named_response, "<h1>人名反应库</h1>", html=True)
        self.assertContains(named_response, "Named Reaction Library")
        self.assertContains(named_response, "人名反应目录")
        self.assertContains(named_response, "全部已发布人名反应")
        self.assertContains(named_response, "Named Only Reaction")
        self.assertNotContains(named_response, "General Only Reaction")
        self.assertContains(general_response, "<h1>常见有机反应库</h1>", html=True)
        self.assertContains(general_response, "General Reaction Library")
        self.assertContains(general_response, "reaction-map-hero--general")
        self.assertContains(general_response, "常见反应目录")
        self.assertContains(general_response, "全部已发布常见反应")
        self.assertContains(general_response, "General Only Reaction")
        self.assertNotContains(general_response, "Named Only Reaction")

    def test_common_reaction_nav_item_is_forced_to_general_library(self):
        NavItem.objects.create(label="人名反应", url_name="reaction_list", sort_order=10)
        NavItem.objects.create(label="常见反应", url_name="reaction_list", sort_order=20)

        response = self.client.get(reverse("home"))

        self.assertContains(response, '<a class="nav-link" href="/reactions/">人名反应</a>', html=True)
        self.assertContains(response, '<a class="nav-link" href="/reactions/general/">常见有机反应</a>', html=True)

    def test_homepage_common_reaction_area_links_to_general_library(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, "General Only Reaction")
        self.assertContains(response, reverse("general_reaction_detail", kwargs={"slug": "general-only-reaction"}))
        self.assertContains(response, reverse("general_reaction_list") + "?tag=exam-high-frequency")
        self.assertContains(response, reverse("general_reaction_list") + "?sort=updated")


class AdminOperationsRedesignTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser("ops-admin", "ops@example.com", "password")
        self.user_a = User.objects.create_user("student-a", "a@example.com", "password")
        self.user_b = User.objects.create_user("student-b", "b@example.com", "password")
        self.client.force_login(self.admin_user)
        self.factory = RequestFactory()

    def _request(self):
        request = self.factory.post("/admin/")
        request.user = self.admin_user
        request._messages = CookieStorage(request)
        return request

    def test_active_announcement_pushes_messages_once(self):
        announcement = Announcement(
            title="课程通知",
            content="今晚更新资料。",
            importance=Announcement.Importance.HIGH,
            is_active=True,
        )
        model_admin = admin.site._registry[Announcement]

        model_admin.save_model(self._request(), announcement, form=None, change=False)
        announcement.refresh_from_db()
        first_count = Message.objects.filter(msg_type=Message.Type.ANNOUNCEMENT, title="课程通知").count()

        model_admin.save_model(self._request(), announcement, form=None, change=True)
        announcement.refresh_from_db()

        self.assertIsNotNone(announcement.message_sent_at)
        self.assertEqual(first_count, User.objects.count())
        self.assertEqual(Message.objects.filter(msg_type=Message.Type.ANNOUNCEMENT, title="课程通知").count(), first_count)

    def test_feedback_reply_and_status_change_notify_user(self):
        feedback = Feedback.objects.create(
            user=self.user_a,
            name="学生A",
            email="a@example.com",
            category=Feedback.Category.CONTENT,
            content="这里有错。",
        )
        feedback.reply = "已经修正。"
        feedback.status = Feedback.Status.RESOLVED
        form = type("FakeForm", (), {"cleaned_data": {"reply": feedback.reply}, "changed_data": ["reply", "status"]})()
        model_admin = admin.site._registry[Feedback]

        model_admin.save_model(self._request(), feedback, form=form, change=True)

        self.assertEqual(Message.objects.filter(recipient=self.user_a, msg_type=Message.Type.FEEDBACK_REPLY).count(), 1)
        self.assertEqual(Message.objects.filter(recipient=self.user_a, msg_type=Message.Type.FEEDBACK_STATUS).count(), 1)

    def test_message_broadcast_page_sends_to_all_users(self):
        response = self.client.post(
            "/admin/operations/messages/send/",
            {
                "target": "all",
                "msg_type": Message.Type.SYSTEM,
                "title": "系统提醒",
                "content": "请查看最新内容。",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "已发送 3")
        self.assertEqual(Message.objects.filter(title="系统提醒").count(), 3)

    def test_message_cleanup_page_deletes_old_read_messages(self):
        old_message = Message.objects.create(
            recipient=self.user_a,
            msg_type=Message.Type.SYSTEM,
            title="旧消息",
            content="旧内容",
            is_read=True,
        )
        Message.objects.filter(pk=old_message.pk).update(created_at="2025-01-01T00:00:00+08:00")
        Message.objects.create(
            recipient=self.user_a,
            msg_type=Message.Type.SYSTEM,
            title="新消息",
            content="新内容",
            is_read=True,
        )

        response = self.client.post(
            "/admin/operations/messages/cleanup/",
            {"older_than": "6", "read_only": "on", "confirm": "on"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "已清理 1")
        self.assertFalse(Message.objects.filter(title="旧消息").exists())
        self.assertTrue(Message.objects.filter(title="新消息").exists())

    def test_setup_admin_roles_command_creates_expected_groups(self):
        call_command("setup_admin_roles", verbosity=0)

        self.assertTrue(Group.objects.filter(name="内容编辑员").exists())
        self.assertTrue(Group.objects.filter(name="运营员").exists())


class V21ContentReadinessTests(TestCase):
    def _complete_reaction_kwargs(self, slug, name_zh):
        return {
            "name_zh": name_zh,
            "name_en": name_zh,
            "slug": slug,
            "summary": "摘要",
            "condition": "条件",
            "exam_tips": "考点",
            "reference": "来源",
            "equation_img": f"reactions/{slug}_equation.svg",
            "thumbnail_img": f"reactions/{slug}_thumbnail.svg",
        }

    def test_homepage_shows_frontend_content_status_counts(self):
        NamedReaction.objects.create(
            **self._complete_reaction_kwargs("published-named-v21", "已发布人名反应"),
            status=PublishStatus.PUBLISHED,
        )
        NamedReaction.objects.create(
            **self._complete_reaction_kwargs("ready-named-v21", "待发布人名反应"),
            status=PublishStatus.DRAFT,
        )
        GeneralReaction.objects.create(
            **self._complete_reaction_kwargs("published-general-v21", "已发布常见反应"),
            status=PublishStatus.PUBLISHED,
        )
        SyntheticRoute.objects.create(
            target_product="已发布路线",
            slug="published-route-v21",
            summary="路线摘要",
            status=PublishStatus.PUBLISHED,
        )

        response = self.client.get(reverse("home"))

        self.assertContains(response, "前台内容状态")
        self.assertContains(response, "已发布人名反应")
        self.assertContains(response, "已发布常见反应")
        self.assertContains(response, "已发布合成路线")
        self.assertContains(response, "待发布完整内容")
        self.assertContains(response, "1 条待发布")

    def test_dashboard_reports_publish_ready_drafts(self):
        NamedReaction.objects.create(
            **self._complete_reaction_kwargs("ready-named-dashboard-v21", "完整人名草稿"),
            status=PublishStatus.DRAFT,
        )
        NamedReaction.objects.create(
            name_zh="缺图人名草稿",
            name_en="缺图人名草稿",
            slug="missing-named-dashboard-v21",
            summary="摘要",
            condition="条件",
            exam_tips="考点",
            reference="来源",
            status=PublishStatus.DRAFT,
        )
        GeneralReaction.objects.create(
            **self._complete_reaction_kwargs("ready-general-dashboard-v21", "完整常见草稿"),
            status=PublishStatus.DRAFT,
        )

        admin_user = User.objects.create_superuser("quality-admin", "quality@example.com", "password")
        self.client.force_login(admin_user)
        response = self.client.get("/admin/reactions/dashboard/")

        self.assertContains(response, "可发布草稿")
        self.assertContains(response, 'id="named-publish-ready">1')
        self.assertContains(response, 'id="general-publish-ready">1')

    def test_publish_ready_content_command_publishes_complete_drafts_only(self):
        ready_named = NamedReaction.objects.create(
            **self._complete_reaction_kwargs("ready-named-command-v21", "命令人名草稿"),
            status=PublishStatus.DRAFT,
        )
        incomplete_named = NamedReaction.objects.create(
            name_zh="命令缺图草稿",
            name_en="命令缺图草稿",
            slug="incomplete-named-command-v21",
            summary="摘要",
            condition="条件",
            exam_tips="考点",
            reference="来源",
            status=PublishStatus.DRAFT,
        )
        ready_general = GeneralReaction.objects.create(
            **self._complete_reaction_kwargs("ready-general-command-v21", "命令常见草稿"),
            status=PublishStatus.DRAFT,
        )
        out = StringIO()

        call_command("publish_ready_content", stdout=out)

        ready_named.refresh_from_db()
        incomplete_named.refresh_from_db()
        ready_general.refresh_from_db()
        self.assertEqual(ready_named.status, PublishStatus.PUBLISHED)
        self.assertEqual(ready_general.status, PublishStatus.PUBLISHED)
        self.assertEqual(incomplete_named.status, PublishStatus.DRAFT)
        self.assertIn("人名反应发布 1 条", out.getvalue())
        self.assertIn("常见有机反应发布 1 条", out.getvalue())

    def test_functional_group_admin_hides_legacy_structure_pattern_field(self):
        admin_user = User.objects.create_superuser("fg-admin", "fg@example.com", "password")
        self.client.force_login(admin_user)

        response = self.client.get(reverse("admin:reactions_functionalgroup_add"))

        self.assertContains(response, "中文名")
        self.assertNotContains(response, "SMARTS")


class V22ReactionImageUploadTests(TestCase):
    def _complete_reaction_kwargs(self, slug, name_zh):
        return {
            "name_zh": name_zh,
            "name_en": name_zh,
            "slug": slug,
            "summary": "摘要",
            "condition": "条件",
            "mechanism": "机理文字",
            "exam_tips": "考点",
            "reference": "来源",
            "thumbnail_img": f"reactions/{slug}_thumbnail.svg",
        }

    def test_reaction_gallery_limits_each_section_to_ten_images(self):
        reaction = NamedReaction.objects.create(**self._complete_reaction_kwargs("multi-image-limit", "多图限制反应"))
        for index in range(10):
            ReactionImage.objects.create(
                content_object=reaction,
                section=ReactionImage.Section.EQUATION,
                image=f"reaction_images/equation_{index}.svg",
            )

        extra = ReactionImage(
            content_object=reaction,
            section=ReactionImage.Section.EQUATION,
            image="reaction_images/equation_extra.svg",
        )

        with self.assertRaises(ValidationError):
            extra.full_clean()

    def test_equation_gallery_image_satisfies_publication_completeness(self):
        reaction = NamedReaction.objects.create(
            **self._complete_reaction_kwargs("gallery-complete", "多方程式反应"),
            status=PublishStatus.DRAFT,
        )
        ReactionImage.objects.create(
            content_object=reaction,
            section=ReactionImage.Section.EQUATION,
            image="reaction_images/gallery_equation.svg",
        )

        self.assertEqual(reaction.get_publication_missing_fields(), [])

    def test_reaction_detail_displays_optional_content_images(self):
        reaction = NamedReaction.objects.create(
            **self._complete_reaction_kwargs("content-images", "内容附图反应"),
            status=PublishStatus.PUBLISHED,
        )
        ReactionImage.objects.create(
            content_object=reaction,
            section=ReactionImage.Section.EQUATION,
            image="reaction_images/equation_a.svg",
            caption="方程式补充图",
        )
        ReactionImage.objects.create(
            content_object=reaction,
            section=ReactionImage.Section.MECHANISM,
            image="reaction_images/mechanism_a.svg",
            caption="机理补充图",
        )
        ReactionImage.objects.create(
            content_object=reaction,
            section=ReactionImage.Section.CONDITION,
            image="reaction_images/condition_a.svg",
            caption="条件说明图",
        )
        ReactionImage.objects.create(
            content_object=reaction,
            section=ReactionImage.Section.MECHANISM_TEXT,
            image="reaction_images/mechanism_text_a.svg",
            caption="机理文字配图",
        )
        ReactionImage.objects.create(
            content_object=reaction,
            section=ReactionImage.Section.EXAM_TIPS,
            image="reaction_images/exam_tip_a.svg",
            caption="考点配图",
        )

        response = self.client.get(reverse("reaction_detail", kwargs={"slug": reaction.slug}))

        self.assertContains(response, "方程式补充图")
        self.assertContains(response, "机理补充图")
        self.assertContains(response, "条件说明图")
        self.assertContains(response, "机理文字配图")
        self.assertContains(response, "考点配图")

    def test_named_reaction_admin_shows_multi_image_upload_inline(self):
        admin_user = User.objects.create_superuser("image-admin", "image@example.com", "password")
        self.client.force_login(admin_user)

        response = self.client.get(reverse("admin:reactions_namedreaction_add"))

        self.assertContains(response, "反应附图上传")
        self.assertContains(response, "每个区域最多 10 张")

    def test_dashboard_treats_equation_gallery_as_available_image(self):
        reaction = NamedReaction.objects.create(
            **self._complete_reaction_kwargs("dashboard-gallery-image", "仪表盘多图反应"),
            status=PublishStatus.DRAFT,
        )
        ReactionImage.objects.create(
            content_object=reaction,
            section=ReactionImage.Section.EQUATION,
            image="reaction_images/dashboard_equation.svg",
        )
        admin_user = User.objects.create_superuser("gallery-admin", "gallery@example.com", "password")
        self.client.force_login(admin_user)

        response = self.client.get("/admin/reactions/dashboard/")

        self.assertContains(response, 'id="named-missing-equation">0')
