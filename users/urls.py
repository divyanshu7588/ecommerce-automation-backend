from django.urls import path
from .views import RegisterView, UserListView, UserDetailView, UserUpdateView, UserDeleteView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('all/', UserListView.as_view(), name='user-list'),
    path('<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
    path('<int:user_id>/update/', UserUpdateView.as_view(), name='user-update'),
    path('<int:user_id>/delete/', UserDeleteView.as_view(), name='user-delete'),
]