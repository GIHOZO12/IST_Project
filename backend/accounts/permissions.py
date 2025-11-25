from rest_framework.permissions import BasePermission


class Is_Staff(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'role', None) == 'staff'


class IsApprover(BasePermission):
    def has_permission(self, request, view):

        return request.user.is_authenticated and getattr(request.user, 'role', None) in [
            'manager_1',
            'manager_2',
            'finance',
        ]


class Is_Finance(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'role', None) == 'finance'

