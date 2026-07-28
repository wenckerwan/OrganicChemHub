# OrganicChemHub 0.2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add content maintenance safeguards and admin efficiency tools for OrganicChemHub 0.2.

**Architecture:** Keep the existing single `reactions` app. Add model-level publication readiness methods and `clean()` validation, then expose those signals through Django Admin list columns and batch actions.

**Tech Stack:** Python 3.11, Django 5.2.x, SQLite, Django Admin.

## Global Constraints

- Work directly in `D:\code_files\OrganicChemHub`.
- Preserve 0.1 public page behavior.
- Do not introduce new external dependencies for 0.2.
- Use TDD for publication validation, content completeness, and admin actions.

---

### Task 1: Publication Readiness Rules

**Files:**
- Modify: `reactions/tests.py`
- Modify: `reactions/models.py`

**Interfaces:**
- Produces: `Reaction.get_publication_missing_fields() -> list[str]`
- Produces: `Reaction.content_completeness() -> str`
- Produces: `SyntheticRoute.get_publication_missing_fields() -> list[str]`
- Produces: `SyntheticRoute.content_completeness() -> str`

- [ ] Write tests that incomplete published reactions fail validation.
- [ ] Write tests that incomplete published routes fail validation when no steps exist.
- [ ] Run the tests and confirm they fail before implementation.
- [ ] Implement readiness and completeness methods.
- [ ] Implement `clean()` methods that raise `ValidationError` for incomplete published content.
- [ ] Run tests until green.

### Task 2: Admin Maintenance Tools

**Files:**
- Modify: `reactions/tests.py`
- Modify: `reactions/admin.py`

**Interfaces:**
- Produces: `ReactionAdmin.publish_selected()`
- Produces: `ReactionAdmin.archive_selected()`
- Produces: `SyntheticRouteAdmin.publish_selected()`
- Produces: `SyntheticRouteAdmin.archive_selected()`
- Produces: admin list columns for content completeness and route step count.

- [ ] Write tests for batch publish skipping incomplete content.
- [ ] Write tests for archive actions setting status to archived.
- [ ] Run the tests and confirm they fail before implementation.
- [ ] Add admin actions and list columns.
- [ ] Add created/updated date hierarchy or filters.
- [ ] Run tests until green.

### Task 3: Verification

**Files:**
- No additional files expected.

- [ ] Run `python manage.py test`.
- [ ] Run `python manage.py check`.
- [ ] Run `python manage.py makemigrations --check --dry-run`.
- [ ] Verify no migration is required for method-only/admin-only changes.
