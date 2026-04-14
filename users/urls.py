from django.urls import path
from .views import RegisterView, LoginView, ProfileView, UserListView, UserDeleteView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('all/', UserListView.as_view(), name='user-list'),
    path('<int:user_id>/delete/', UserDeleteView.as_view(), name='user-delete'),
]