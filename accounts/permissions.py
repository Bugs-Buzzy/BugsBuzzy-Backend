from rest_framework.permissions import BasePermission


class IsVerified(BasePermission):
    """
    Custom permission to only allow verified users to access the view.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_verified
        )


class ProfileCompleted(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_verified and
            request.user.profile_completed
        )