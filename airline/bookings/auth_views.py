from django.contrib.auth.views import LoginView
from django.contrib import messages

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    
    def form_invalid(self, form):
        messages.error(self.request, 'Invalid login credentials. Please check your username and password and try again.')
        return super().form_invalid(form)