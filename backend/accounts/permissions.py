from  rest_framework.permissions import BasePermission



class Is_Staff(BasePermission):
    def is_staff(self, user, view):
        return user.role == 'staff'



class IsApprover(BasePermission):
    def is_approve(self, request, view):
        return request.user.role in ['approver_level_1', 'approver_level_2']



class Is_Finance(BasePermission):
    def is_finance(self, request, view):
        return request.user.role == 'finance'



