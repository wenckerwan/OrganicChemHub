from django.urls import path

from .views import (
    DeployGuideView,
    HomeView,
    LearningResourceListView,
    ReactionDetailView,
    ReactionListView,
    RouteDetailView,
    RouteListView,
)


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("deploy/", DeployGuideView.as_view(), name="deploy_guide"),
    path("reactions/", ReactionListView.as_view(), name="reaction_list"),
    path("reactions/<slug:slug>/", ReactionDetailView.as_view(), name="reaction_detail"),
    path("routes/", RouteListView.as_view(), name="route_list"),
    path("routes/<slug:slug>/", RouteDetailView.as_view(), name="route_detail"),
    path("learning-resources/", LearningResourceListView.as_view(), name="learning_resource_list"),
]
