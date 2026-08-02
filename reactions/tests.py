from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.contrib.messages.storage.cookie import CookieStorage
from django.test import RequestFactory
from django.test import TestCase
from django.urls import reverse
from pathlib import Path
from tempfile import TemporaryDirectory

from reactions.admin import ReactionAdmin, SyntheticRouteAdmin
from reactions.models import (
    FunctionalGroup,
    GeneralReaction,
    GeneralReactionCategory,
    LearningResource,
    NamedReaction,
    NamedReactionCategory,
    PublishStatus,
    Reaction,
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
        self.assertIn(Reaction, admin.site._registry)
        self.assertIn(ReactionType, admin.site._registry)
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
        Reaction.objects.create(
            name_zh="未发布反应",
            name_en="Hidden Reaction",
            slug="hidden-reaction",
            reaction_type=self.reaction_type,
            status=Reaction.Status.DRAFT,
        )
        self.route = SyntheticRoute.objects.create(
            target_product="苯乙酮",
            target_structure_image_url="/static/img/reactions/lecture_002.png",
            slug="acetophenone",
            summary="从苯出发的基础路线。",
            status=SyntheticRoute.Status.PUBLISHED,
        )
        self.route.related_reactions.add(self.reaction)
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

    def test_reaction_list_searches_name_and_condition(self):
        response = self.client.get(reverse("reaction_list"), {"q": "膦叶立德"})

        self.assertContains(response, "维蒂希反应")
        self.assertNotContains(response, "未发布反应")

    def test_reaction_list_uses_reference_browser_layout(self):
        response = self.client.get(reverse("reaction_list"))

        self.assertContains(response, 'class="reaction-browser"')
        self.assertContains(response, 'class="reaction-browser__sidebar"')
        self.assertContains(response, 'class="reaction-browser__content"')
        self.assertContains(response, "已收录在化学学习中常见的人名反应")

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
        self.assertContains(response, 'src="/static/img/reactions/lecture_001.png"')
        self.assertContains(response, "讲义结构式示例")

    def test_reaction_detail_shows_fallback_when_no_image(self):
        self.reaction.structure_image_url = ""
        self.reaction.save(update_fields=["structure_image_url"])

        response = self.client.get(reverse("reaction_detail", kwargs={"slug": "wittig-reaction"}))

        self.assertNotContains(response, 'src="/static/img/reactions/lecture_001.png"')

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
        self.assertContains(response, "Diels-Alder")

    def test_exam_reactions_fixture_adds_common_postgraduate_reactions(self):
        call_command("loaddata", "common_reactions", "exam_reactions", verbosity=0)

        self.assertGreaterEqual(Reaction.published.count(), 40)
        response = self.client.get(reverse("reaction_list"), {"q": "Sandmeyer"})
        self.assertContains(response, "Sandmeyer Reaction")
        self.assertContains(response, "重氮盐")


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
