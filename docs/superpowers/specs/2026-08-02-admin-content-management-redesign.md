# OrganicChemHub Admin Content Management Redesign

## Goal

Redesign OrganicChemHub's next backend content management version around a hybrid admin architecture: Django Admin remains the standard editing surface, while complex operational workflows move into dedicated admin tool pages.

This version focuses on backend content management. Existing frontend visual design should be preserved as much as practical, but model structure and view data access may change. Existing production data does not need to be migrated.

## Confirmed Scope

Primary modules:

- Named reactions.
- General organic reactions.
- Synthetic routes.
- Reaction categories.
- Announcements.
- Feedback.
- Site messages.

Secondary module:

- Learning resources, kept lightweight and functional.

Explicit decisions:

- Use Django Admin as the primary backend editing surface.
- Add dedicated admin tool pages for complex workflows.
- Keep named reactions and general organic reactions as separate models.
- Keep named reaction categories and general reaction categories as separate models.
- Do not design the system around SMILES in this version.
- Do not require old data migration.
- Preserve the current frontend UI style where possible.

## Architecture

The backend has two layers.

### Standard Content Management Layer

Django Admin handles frequent, stable, structured editing:

- Named reactions.
- General organic reactions.
- Synthetic routes and route steps.
- Named reaction categories.
- General reaction categories.
- Tags.
- Functional groups.
- Learning resources.
- Announcements.
- Feedback.
- Site messages.

Admin pages should be tuned for non-technical editors:

- Clear field grouping.
- Helpful field descriptions.
- Image thumbnails in list views.
- Image previews in edit forms.
- Consistent status filtering.
- Bulk publish and archive actions.
- Search on editor-friendly fields.
- Content completeness indicators.

### Dedicated Admin Tool Layer

Dedicated admin pages handle workflows that do not fit cleanly inside regular model CRUD:

- Content quality dashboard.
- CSV import.
- Image maintenance.
- Message broadcast.
- Learning resource upload/path registration.
- Old message cleanup.

## Core Data Model Design

### NamedReaction

Named reactions are a standalone content library for name reactions.

Core fields:

- Chinese name.
- English name.
- Aliases.
- Slug.
- Status: draft, published, archived.
- Named reaction category.
- Tags.
- Functional groups.
- Summary.
- Reaction conditions.
- Mechanism description.
- Exam tips.
- Scope.
- Limitations.
- Reference.
- Equation image.
- Mechanism image.
- Thumbnail image.
- Created time.
- Updated time.

Image rules:

- Equation image is supported.
- Thumbnail image is supported.
- Mechanism image is supported but optional.
- Mechanism image is not required for completeness because some reactions do not require mechanism mastery.
- Uploaded images are renamed automatically using a stable convention based on reaction slug and image type.
- List views show thumbnail previews.
- Edit views show image previews.

Completeness rules:

- Required for content quality: summary, reaction conditions, exam tips, reference, equation image, thumbnail image.
- Optional: mechanism image, mechanism description, scope, limitations.
- The admin list should show both a completeness ratio and a readable missing-field summary.

### GeneralReaction

General organic reactions are a separate content library for common non-name reactions such as addition, substitution, elimination, oxidation, reduction, condensation, rearrangement, and related reaction families.

Core fields mirror NamedReaction, but use GeneralReactionCategory instead of NamedReactionCategory.

Image and completeness rules match NamedReaction:

- Equation image and thumbnail image count toward required completeness.
- Mechanism image is optional.
- Uploaded images are automatically renamed.
- Admin list and edit pages show previews.

### Reaction Categories

The category system is intentionally split:

- NamedReactionCategory: categories only for named reactions.
- GeneralReactionCategory: categories only for general organic reactions.

Each category includes:

- Name.
- Slug.
- Description.
- Sort order.
- Active flag.

Tags and functional groups remain shared dimensions:

- Tags are flexible editorial labels such as exam-high-frequency, classic, easy-to-confuse, must-remember.
- Functional groups describe structural relevance such as aldehyde, ketone, ester, alkene, alkyne, aromatic ring.

### SyntheticRoute

Synthetic routes remain an independent module with route steps managed inline.

SyntheticRoute fields:

- Target product name.
- Slug.
- Target product structure image.
- Summary.
- Difficulty.
- Advantages.
- Disadvantages.
- Source.
- Status.
- Related named reactions.
- Related general reactions.
- Created time.
- Updated time.

RouteStep fields:

- Parent route.
- Step number.
- Title.
- Reactant structure image.
- Product structure image.
- Reagents.
- Conditions.
- Yield text.
- Note.
- Related named reactions.
- Related general reactions.

Publishing rule:

- Route requires target product name, summary, and at least one route step before publishing.

### LearningResource

Learning resources are retained as a secondary module with dual-source support.

Fields:

- Title.
- Category.
- Year.
- File type.
- Has answer.
- Source type: uploaded file or external path.
- Uploaded file.
- External path.
- Status.
- Created time.
- Updated time.

Rules:

- Uploaded file and external path are alternatives.
- At least one source must be present before publishing.
- File type can be derived from the uploaded file or external path when possible.

### Announcement

Fields:

- Title.
- Content.
- Importance: normal or important.
- Pinned flag.
- Active flag.
- Display start time.
- Display end time.
- Created time.

Behavior:

- Active announcements display in the homepage announcement bar.
- Important active announcements may trigger a frontend modal.
- Pinned announcements ignore display time limits.
- Publishing or activating an announcement sends site messages to registered users.
- Re-saving unchanged active announcements should avoid duplicate message storms.
- Frontend dismissal should avoid repeatedly showing the same important announcement.

### Feedback

Fields:

- User, optional.
- Name.
- Email.
- Category: content correction, feature suggestion, data supplement, usage question, other.
- Content.
- Status: pending, processing, resolved, closed.
- Admin reply.
- Internal note.
- Handled by.
- Handled at.
- Read flag.
- Created time.

Behavior:

- Admin replies are visible to the submitting user when tied to an account.
- Internal notes are admin-only.
- Reply creation sends a site message.
- Status changes send a site message.
- Bulk actions: mark read, mark processing, mark resolved, mark closed.

### Message

Fields:

- Recipient.
- Message type: announcement, feedback reply, feedback status, review notice, system.
- Title.
- Content.
- Read flag.
- Related URL.
- Created time.

Broadcast and cleanup workflows live in dedicated tool pages.

### Operation Log

Fields:

- User.
- Action.
- Model name.
- Object representation.
- Detail.
- IP address.
- Created time.

Logged actions:

- Create, update, delete.
- Bulk publish.
- Bulk archive.
- CSV import.
- Image maintenance.
- Message broadcast.
- Message cleanup.

Logs are read-only.

## Django Admin Design

### Named Reaction Admin

List display:

- Chinese name.
- English name.
- Category.
- Thumbnail.
- Status.
- Completeness.
- Missing fields.
- Updated time.

Search:

- Chinese name.
- English name.
- Aliases.

Filters:

- Category.
- Tags.
- Functional groups.
- Status.
- Created time.
- Updated time.

Actions:

- Publish selected.
- Archive selected.
- Export selected as CSV.

Edit sections:

- Basic information.
- Classification.
- Content.
- Images.
- Publishing.
- Timestamps.

### General Reaction Admin

GeneralReaction admin mirrors NamedReaction admin, but uses GeneralReactionCategory.

### Synthetic Route Admin

List display:

- Target product.
- Difficulty.
- Status.
- Source.
- Related named reaction count.
- Related general reaction count.
- Step count.
- Updated time.

Search:

- Target product.
- Summary.
- Source.

Filters:

- Difficulty.
- Status.
- Related named reactions.
- Related general reactions.

Actions:

- Publish selected.
- Archive selected.
- Export selected as CSV.

RouteStep inline appears below route fields.

### Category, Tag, Functional Group Admin

Category list display:

- Name.
- Slug.
- Sort order.
- Active flag.

Tag and functional group admin remain lightweight, with search and simple list editing.

### Learning Resource Admin

List display:

- Title.
- Category.
- Year.
- Source type.
- File type.
- Has answer.
- Status.
- Updated time.

Search:

- Title.
- External path.

Filters:

- Category.
- Source type.
- Has answer.
- Status.
- Year.

Actions:

- Publish selected.
- Archive selected.
- Export selected as CSV.

### Announcement Admin

List display:

- Title.
- Importance.
- Pinned flag.
- Active flag.
- Display start time.
- Display end time.
- Created time.

Saving an active announcement triggers message creation when appropriate, without duplicate storms.

### Feedback Admin

List display:

- Category.
- Submitter.
- Email.
- Content summary.
- Status.
- Read flag.
- Created time.

Filters:

- Category.
- Status.
- Read flag.
- Created time.

Actions:

- Mark read.
- Mark processing.
- Mark resolved.
- Mark closed.

Edit form:

- Submitted feedback section is read-only.
- Admin reply is editable.
- Internal note is editable.
- Status is editable.

### Message Admin

List display:

- Recipient.
- Message type.
- Title.
- Read flag.
- Created time.

Filters:

- Message type.
- Read flag.
- Created time.

Search:

- Recipient username.
- Title.
- Content.

Actions:

- Mark read.

Broadcast and cleanup are dedicated tool pages.

## Dedicated Admin Tool Pages

### Content Quality Dashboard

Path:

- `/admin/reactions/dashboard/`

Shows:

- Named reaction totals by status.
- General reaction totals by status.
- Missing equation image counts.
- Missing thumbnail image counts.
- Field missing rates for summary, conditions, exam tips, reference, equation image, thumbnail image.
- Synthetic route totals.
- Routes missing steps.
- Content count by named reaction category.
- Content count by general reaction category.
- Recently updated content.

### CSV Import

Path:

- `/admin/reactions/import/`

Supports:

- Named reaction CSV import.
- General reaction CSV import.

Flow:

1. Upload CSV.
2. Preview parsed rows.
3. Show validation errors before writing.
4. Select create-only or update-existing mode.
5. Execute import.
6. Show created, updated, skipped, and error counts.

Matching:

- Chinese name plus English name.

Invalid rows are skipped with visible error details.

### Image Maintenance

Path:

- `/admin/reactions/images/`

Supports:

- List named reactions missing equation images.
- List named reactions missing thumbnail images.
- List general reactions missing equation images.
- List general reactions missing thumbnail images.
- Show reactions with non-standard image names.
- Batch rename uploaded images to standard convention.
- Optional thumbnail generation from equation image if image tooling is available.

Mechanism images are optional and not included in mandatory missing-image counts.

### Message Broadcast

Path:

- `/admin/operations/messages/send/`

Supports:

- Send to all users.
- Send to selected users.
- Select message type.
- Enter title and content.
- Preview recipient count.
- Confirm before sending.
- Log broadcast.

### Learning Resource Upload And Registration

Path:

- `/admin/resources/import-or-upload/`

Supports:

- Upload one or more resource files.
- Register one or more external paths.
- Set category, year, answer flag, and status.
- Infer file type where possible.
- Create LearningResource records.

### Message Cleanup

Path:

- `/admin/operations/messages/cleanup/`

Supports:

- Clean read messages older than 3 months, 6 months, or 1 year.
- Preview deletion count.
- Require confirmation before delete.
- Log cleanup action.

## Permissions

Use Django built-in groups and model permissions.

### Super Administrator

Can:

- Manage all models.
- Use all dedicated tools.
- Manage users, groups, and permissions.
- Clean old messages.

### Content Editor

Can:

- Manage named reactions.
- Manage general reactions.
- Manage synthetic routes and steps.
- Manage reaction categories.
- Manage tags and functional groups.
- Manage learning resources.
- Use quality dashboard.
- Use CSV import.
- Use image maintenance tools.

Cannot:

- Manage users.
- Change groups or permissions.
- Reply to feedback as an operator.
- Broadcast messages.
- Clean old messages.

### Operations Staff

Can:

- Manage announcements.
- Manage feedback.
- Manage site messages.
- Use message broadcast.

Cannot:

- Modify reaction content.
- Modify route content.
- Modify reaction categories.
- Manage users or permissions.

## Frontend Compatibility

Frontend UI style remains broadly unchanged.

Required adaptation:

- Existing named reaction list/detail pages read from the new named reaction model.
- General organic reactions get list/detail pages reusing current reaction page visual style.
- Synthetic route pages support related named reactions and related general reactions.
- Learning resources remain available as a lightweight list.
- Only published content is shown publicly.
- Missing optional mechanism images do not render empty sections.

Recommendation:

- Add small query/helper functions for public content retrieval so templates depend less on model internals.

## Testing Strategy

### Model Tests

Cover:

- Named reaction completeness.
- General reaction completeness.
- Mechanism image optional behavior.
- Image upload naming.
- Published manager filtering.
- Route publish validation requiring at least one step.
- Learning resource publish validation requiring either upload or external path.

### Admin Tests

Cover:

- Model registration.
- List pages load.
- Bulk publish/archive.
- CSV export fields.
- Route step inline configuration.
- Feedback reply message creation.
- Announcement message creation without duplicate storms.
- Permission group access boundaries.

### Tool Page Tests

Cover:

- Dashboard totals.
- CSV preview validation.
- CSV create/update modes.
- Image missing lists.
- Image rename logging.
- Message broadcast recipient count and creation.
- Message cleanup preview and confirmed deletion.

### Frontend Tests

Cover:

- Named reaction list/detail pages.
- General reaction list/detail pages.
- Synthetic route list/detail pages.
- Learning resource list page.
- Draft and archived content not appearing publicly.
- Missing optional mechanism image does not render broken section.

## Acceptance Criteria

The version is complete when a non-technical editor can:

- Create and publish a named reaction.
- Upload a named reaction equation image and thumbnail image.
- Leave a mechanism image empty without blocking publish.
- Create and publish a general organic reaction.
- Maintain separate named reaction and general reaction categories.
- Create a synthetic route and edit its steps inline.
- Associate routes and route steps with named reactions and general reactions.
- Use the quality dashboard to find missing content and missing required images.
- Import named reactions and general reactions from CSV through an admin page.
- Use image maintenance to identify required missing images.
- Publish an announcement and send site messages.
- Reply to feedback and notify the user.
- View operation logs for key admin actions.
- Use the existing frontend visual experience against the new data structure.
