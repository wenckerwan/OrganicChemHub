"""Re-exports all views for URL configuration."""
from .home import DeployGuideView, HomeView
from .auth import ProfileView, RegisterView
from .reactions import (
    CommonReactionListView,
    GeneralReactionDetailView,
    GeneralReactionListView,
    ReactionDetailView,
    ReactionListView,
    ToggleFavoriteView,
    UpdateProgressView,
)
from .routes import RouteDetailView, RouteListView, SaveNoteView
from .feedback import (
    FeedbackView,
    LearningResourceListView,
    MarkAllMessagesReadView,
    MessageDetailView,
    MessageListView,
)
