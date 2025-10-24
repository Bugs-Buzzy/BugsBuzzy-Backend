from rest_framework.permissions import BasePermission


class IsVerified(BasePermission):
    """
    Custom permission to only allow verified users to access the view.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_verified


class ProfileCompleted(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_verified
            and request.user.profile_completed
        )


class HasPaid(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_verified
            and request.user.profile_completed
            and request.user.has_paid
        )


def HasPurchased(item_name):
    """Factory function to create permission class that checks if user has purchased specific item"""
    
    class _HasPurchasedItem(BasePermission):
        def has_permission(self, request, view):
            if not (request.user and request.user.is_authenticated and request.user.is_verified and request.user.profile_completed):
                return False
            
            from payments.models import Transaction
            import json
            
            # Check if user has completed transaction with specified item
            completed_transactions = Transaction.objects.filter(
                user=request.user,
                status='completed'
            )
            
            for trans in completed_transactions:
                if trans.items:
                    try:
                        items = json.loads(trans.items)
                        if item_name in items:
                            return True
                    except (json.JSONDecodeError, TypeError):
                        pass
            
            return False
    
    return _HasPurchasedItem
