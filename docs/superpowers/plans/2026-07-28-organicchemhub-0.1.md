# OrganicChemHub 0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build OrganicChemHub 0.1 as a usable Django site for browsing, searching, and administering organic name reactions and synthetic routes.

**Architecture:** Use a single Django project with one `reactions` app for the first version. The app owns models, admin configuration, search views, and templates for reactions and synthetic routes. SQLite is used locally, with fields and settings kept portable for later PostgreSQL migration.

**Tech Stack:** Python 3.11, Django 5.2.x, SQLite, Django templates, Bootstrap 5 via CDN.

## Global Constraints

- Develop directly in `D:\code_files\OrganicChemHub`.
- Version 0.1 implements only foundational features: reaction database, route database, admin CRUD, search/list/detail pages, and basic tests.
- Do not implement RDKit, Ketcher, user accounts, notes, or API endpoints in 0.1.
- Keep data structures compatible with later structure rendering and route-step expansion.

---

### Task 1: Project Bootstrap

**Files:**
- Create: `requirements.txt`
- Create: `manage.py`
- Create: `organic_chem_hub/settings.py`
- Create: `organic_chem_hub/urls.py`
- Create: `organic_chem_hub/wsgi.py`
- Create: `organic_chem_hub/asgi.py`
- Create: `reactions/apps.py`

**Interfaces:**
- Produces: Django project named `organic_chem_hub`
- Produces: app named `reactions`

- [ ] Create a local virtual environment at `.venv`.
- [ ] Install dependencies from `requirements.txt`.
- [ ] Add Django settings with SQLite, templates, static files, and `reactions`.
- [ ] Run `python manage.py check`.

### Task 2: Core Data Models

**Files:**
- Create: `reactions/models.py`
- Create: `reactions/tests.py`
- Create: `reactions/migrations/__init__.py`

**Interfaces:**
- Produces: `ReactionType`, `Tag`, `FunctionalGroup`, `Reaction`, `SyntheticRoute`, `RouteStep`
- Produces: status constants `draft`, `published`, `archived`

- [ ] Write tests for model string output, relationships, route step ordering, and published filtering.
- [ ] Run tests and confirm they fail before model implementation.
- [ ] Implement models with slug, status, timestamps, and relationships.
- [ ] Run tests until they pass.
- [ ] Create migrations.

### Task 3: Admin CRUD

**Files:**
- Create: `reactions/admin.py`

**Interfaces:**
- Consumes: all models from `reactions.models`
- Produces: Django Admin maintenance screens

- [ ] Write admin registration tests.
- [ ] Run tests and confirm missing admin registration fails.
- [ ] Register models with search, filters, inlines, readonly fields, and many-to-many widgets.
- [ ] Run tests until they pass.

### Task 4: Public Pages

**Files:**
- Create: `reactions/views.py`
- Create: `reactions/urls.py`
- Modify: `organic_chem_hub/urls.py`
- Create: `templates/base.html`
- Create: `templates/reactions/home.html`
- Create: `templates/reactions/reaction_list.html`
- Create: `templates/reactions/reaction_detail.html`
- Create: `templates/reactions/route_list.html`
- Create: `templates/reactions/route_detail.html`

**Interfaces:**
- Produces: named URLs `home`, `reaction_list`, `reaction_detail`, `route_list`, `route_detail`
- Produces: public pages showing only published content

- [ ] Write view tests for homepage, reaction search, detail pages, route search, and unpublished filtering.
- [ ] Run tests and confirm failures before view/template implementation.
- [ ] Implement views using Django generic class-based views.
- [ ] Implement templates with Bootstrap 5 layout.
- [ ] Run tests until they pass.

### Task 5: Developer Usability

**Files:**
- Create: `README.md`
- Create: `.gitignore`

**Interfaces:**
- Produces: setup and run instructions for GitHub syncing and local development

- [ ] Add README with setup, migrate, create admin, run server, and test commands.
- [ ] Add `.gitignore` for Python, Django, SQLite, and virtual environment artifacts.
- [ ] Run the full test suite and `manage.py check`.
