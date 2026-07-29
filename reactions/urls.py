from django.urls import path

from .views import (
    DeployGuideView,
    FeedbackView,
    HomeView,
    LearningResourceListView,
    ProfileView,
    ReactionDetailView,
    ReactionListView,
    RegisterView,
    RouteDetailView,
    RouteListView,
    SaveNoteView,
    ToggleFavoriteView,
    UpdateProgressView,
)


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("feedback/", FeedbackView.as_view(), name="feedback"),
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("favorite/toggle/", ToggleFavoriteView.as_view(), name="toggle_favorite"),
    path("note/save/", SaveNoteView.as_view(), name="save_note"),
    path("progress/update/", UpdateProgressView.as_view(), name="update_progress"),
    path("deploy/", DeployGuideView.as_view(), name="deploy_guide"),
    path("reactions/", ReactionListView.as_view(), name="reaction_list"),
    path("reactions/<slug:slug>/", ReactionDetailView.as_view(), name="reaction_detail"),
    path("routes/", RouteListView.as_view(), name="route_list"),
    path("routes/<slug:slug>/", RouteDetailView.as_view(), name="route_detail"),
    path("learning-resources/", LearningResourceListView.as_view(), name="learning_resource_list"),
]
