from django.contrib.auth import views as auth
from django.urls import path, reverse_lazy
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth.LoginView.as_view(template_name='accounts/form.html', extra_context={'title': 'Good to see you.', 'eyebrow': 'WELCOME BACK', 'button': 'Sign in', 'mode': 'login'}), name='login'),
    path('logout/', auth.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('password-reset/', auth.PasswordResetView.as_view(template_name='accounts/form.html', email_template_name='accounts/reset_email.txt', subject_template_name='accounts/reset_subject.txt', extra_context={'title': 'A fresh start.', 'eyebrow': 'RESET PASSWORD', 'button': 'Send reset link'}), name='password_reset'),
    path('password-reset/sent/', auth.PasswordResetDoneView.as_view(template_name='accounts/reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth.PasswordResetConfirmView.as_view(template_name='accounts/reset_confirm.html', success_url=reverse_lazy('password_reset_complete')), name='password_reset_confirm'),
    path('reset/complete/', auth.PasswordResetCompleteView.as_view(template_name='accounts/reset_complete.html'), name='password_reset_complete'),
]

