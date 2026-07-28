# OrganicChemHub 0.3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve search and classification so reactions, routes, and learning resources are easier to find and scan.

**Architecture:** Keep model schema stable. Add a small search utility layer for query-string preservation and result highlighting, then enhance list views and templates with filtering, sorting, quick exam filters, empty-result recommendations, and highlight rendering.

**Tech Stack:** Python 3.11, Django 5.2.x, SQLite, Django templates, Bootstrap 5.

## Global Constraints

- Preserve 0.1, 0.2, and 0.25 behavior.
- Do not add external dependencies.
- Do not add database fields for 0.3.
- Use tests before implementation for filtering, sorting, highlighting, recommendations, and pagination state.

---

### Task 1: Search Utilities

**Files:**
- Create: `reactions/services/search.py`
- Create: `reactions/templatetags/search_extras.py`
- Modify: `reactions/tests.py`

**Interfaces:**
- Produces: `build_querystring(querydict, **updates) -> str`
- Produces: template filter `highlight_query(value, query)`

- [ ] Write tests for query-string preservation.
- [ ] Write tests for safe keyword highlighting.
- [ ] Implement utility and template tag.
- [ ] Verify tests pass.

### Task 2: Reaction Search Enhancements

**Files:**
- Modify: `reactions/views.py`
- Modify: `templates/reactions/reaction_list.html`
- Modify: `templates/reactions/partials/reaction_card.html`

**Interfaces:**
- Produces: `functional_group` filter.
- Produces: `exam=1` quick filter.
- Produces: `sort` options `name`, `type`, `updated`.
- Produces: empty-result recommendations.

- [ ] Write tests for functional-group filtering.
- [ ] Write tests for exam quick filter.
- [ ] Write tests for reaction sorting.
- [ ] Write tests for empty-result recommendations.
- [ ] Implement view and template updates.

### Task 3: Route and Resource Search Enhancements

**Files:**
- Modify: `reactions/views.py`
- Modify: `templates/reactions/route_list.html`
- Modify: `templates/reactions/learning_resource_list.html`

**Interfaces:**
- Produces: route sorting by `target`, `difficulty`, `steps`, `updated`.
- Produces: resource sorting by `title`, `year`, `category`, `size`, `updated`.
- Produces: empty-result recommendations.

- [ ] Write tests for route step-count sorting.
- [ ] Write tests for resource year sorting.
- [ ] Implement view and template updates.

### Task 4: Verification and Docs

**Files:**
- Modify: `README.md`
- Modify: `static/css/site.css`

- [ ] Update README with 0.3 summary.
- [ ] Add lightweight styles for highlighted terms and recommendation panels.
- [ ] Run `python manage.py test`.
- [ ] Run `python manage.py check`.
- [ ] Run `python manage.py makemigrations --check --dry-run`.
