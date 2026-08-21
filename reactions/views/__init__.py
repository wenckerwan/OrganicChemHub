"""Re-exports all views for URL configuration."""
from .home import DeployGuideView, HomeView, robots_txt_view
from .auth import ProfileView, RegisterView
from .reactions import (
    CommonReactionListView,
    GeneralReactionDetailView,
    GeneralReactionListView,
    ReactionDetailView,
    ReactionListView,
    SubmitCommentView,
    ToggleFavoriteView,
    UpdateProgressView,
)
from .routes import RouteDetailView, RouteListView, SaveNoteView
from .study import (
    ReactionComparisonDetailView,
    ReactionComparisonListView,
    StudyTopicDetailView,
    StudyTopicListView,
)
from .feedback import (
    FeedbackView,
    LearningResourceListView,
    MarkAllMessagesReadView,
    MessageDetailView,
    MessageListView,
)
