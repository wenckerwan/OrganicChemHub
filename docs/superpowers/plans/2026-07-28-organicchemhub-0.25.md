# OrganicChemHub 0.25 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add first-deployment onboarding, Baota Panel deployment guidance, common named reaction seed data, and a local learning-resource index for exam/practice materials.

**Architecture:** Keep the existing Django app. Add public onboarding and learning-resource pages, a `LearningResource` model for metadata-only indexing, management commands for scanning local resources, and fixtures for common named reactions.

**Tech Stack:** Python 3.11, Django 5.2.x, SQLite, Django templates, Bootstrap 5.

## Global Constraints

- Work directly in `D:\code_files\OrganicChemHub`.
- The learning materials root is `F:\2027考研资料\有机化学`.
- Do not copy, publish, or extract full copyrighted document content into the public site.
- Store learning resources as metadata and local paths only; the first version should not expose direct file downloads.
- Preserve all 0.1 and 0.2 behavior.

---

### Task 1: First Deployment Onboarding

**Files:**
- Modify: `reactions/tests.py`
- Modify: `reactions/views.py`
- Modify: `reactions/urls.py`
- Modify: `templates/base.html`
- Create: `templates/reactions/deploy_guide.html`

**Interfaces:**
- Produces: URL name `deploy_guide`
- Produces: public path `/deploy/`

- [ ] Write tests that `/deploy/` returns deployment checklist content.
- [ ] Implement view and template.
- [ ] Add navigation link.
- [ ] Verify tests pass.

### Task 2: Baota Panel Deployment Guidance

**Files:**
- Create: `docs/deploy_baota_panel.md`
- Modify: `README.md`

**Interfaces:**
- Produces: Baota Panel deployment instructions for Python project hosting, Gunicorn, Nginx reverse proxy, static files, environment variables, migration, and backup.

- [ ] Write deployment doc.
- [ ] Link it from README.
- [ ] Include first deployment checklist and common troubleshooting.

### Task 3: Common Named Reaction Seed Data

**Files:**
- Create: `reactions/fixtures/common_reactions.json`
- Modify: `README.md`

**Interfaces:**
- Produces: seed data with common named reactions in published status.

- [ ] Write tests that loading common reaction fixture makes at least 10 published reactions searchable.
- [ ] Create fixture with common reaction types, tags, functional groups, and reactions.
- [ ] Verify fixture loads cleanly.

### Task 4: Learning Resource Index

**Files:**
- Modify: `reactions/models.py`
- Modify: `reactions/admin.py`
- Modify: `reactions/views.py`
- Modify: `reactions/urls.py`
- Create: `templates/reactions/learning_resource_list.html`
- Create: `reactions/management/commands/index_learning_resources.py`
- Create migration for `LearningResource`

**Interfaces:**
- Produces: `LearningResource` model with title, category, year, file type, size, local path, relative path, answer flag, source folder, and status.
- Produces: URL name `learning_resource_list`
- Produces: public path `/learning-resources/`

- [ ] Write model and view tests.
- [ ] Write command tests using a temporary directory.
- [ ] Implement model, admin, view, template, and command.
- [ ] Generate migration.
- [ ] Scan `F:\2027考研资料\有机化学` into the local database.

### Task 5: Verification

**Files:**
- No additional files expected.

- [ ] Run `python manage.py test`.
- [ ] Run `python manage.py check`.
- [ ] Run `python manage.py makemigrations --check --dry-run`.
- [ ] Run `python manage.py migrate`.
- [ ] Verify `/deploy/` and `/learning-resources/` return 200.
