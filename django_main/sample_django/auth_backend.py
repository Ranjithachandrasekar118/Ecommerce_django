from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from .models import UserProfile

class ContactNumberAuthBackend(ModelBackend):
    """
    Custom authentication backend to allow login with contact number
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Allow authentication with either username or contact number
        """
        # Check if username is actually a contact number
        try:
            # Try to find user by contact number
            profile = UserProfile.objects.get(contact_number=username)
            user = profile.user
            if user.check_password(password):
                return user
        except UserProfile.DoesNotExist:
            pass
        
        # Fall back to username authentication
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
