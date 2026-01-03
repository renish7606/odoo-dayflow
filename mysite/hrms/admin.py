from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Profile, Attendance, LeaveRequest, Payroll


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Custom user admin with employee ID and role"""
    list_display = ['employee_id', 'username', 'email', 'role', 'email_verified', 'is_active']
    list_filter = ['role', 'email_verified', 'is_active', 'date_joined']
    search_fields = ['employee_id', 'username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Employee Information', {
            'fields': ('employee_id', 'role', 'email_verified', 'verification_token')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Employee Information', {
            'fields': ('employee_id', 'role', 'email')
        }),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Profile admin"""
    list_display = ['user', 'designation', 'department', 'employment_type', 'date_of_joining']
    list_filter = ['department', 'employment_type', 'date_of_joining']
    search_fields = ['user__employee_id', 'user__first_name', 'user__last_name', 'designation']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """Attendance admin"""
    list_display = ['user', 'date', 'check_in_time', 'check_out_time', 'status', 'total_hours']
    list_filter = ['status', 'date']
    search_fields = ['user__employee_id', 'user__first_name', 'user__last_name']
    date_hierarchy = 'date'
    ordering = ['-date']


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    """Leave request admin"""
    list_display = ['user', 'leave_type', 'start_date', 'end_date', 'status', 'approved_by']
    list_filter = ['status', 'leave_type', 'created_at']
    search_fields = ['user__employee_id', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    actions = ['approve_leaves', 'reject_leaves']
    
    def approve_leaves(self, request, queryset):
        queryset.update(status='APPROVED', approved_by=request.user)
        self.message_user(request, f"{queryset.count()} leave requests approved.")
    approve_leaves.short_description = "Approve selected leave requests"
    
    def reject_leaves(self, request, queryset):
        queryset.update(status='REJECTED', approved_by=request.user)
        self.message_user(request, f"{queryset.count()} leave requests rejected.")
    reject_leaves.short_description = "Reject selected leave requests"


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    """Payroll admin"""
    list_display = ['user', 'basic_salary', 'gross_salary', 'total_deductions', 'net_salary', 'effective_date']
    list_filter = ['effective_date']
    search_fields = ['user__employee_id', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'effective_date'
