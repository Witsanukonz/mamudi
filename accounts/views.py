from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .forms import ProfileForm, RegisterForm


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Welcome to MAMUDI. Your account is ready.')
        return redirect('home')
    return render(request, 'accounts/form.html', {'form': form, 'title': 'Make yourself at home.', 'eyebrow': 'JOIN MAMUDI', 'button': 'Create account', 'mode': 'register'})


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Your profile has been updated.')
        return redirect('profile')
    return render(request, 'accounts/form.html', {'form': form, 'title': 'Your details.', 'eyebrow': 'MY ACCOUNT', 'button': 'Save changes'})

