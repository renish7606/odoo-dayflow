from django.urls import path
from . import views


urlpatterns = [
    # Authentication URLs
    path('signup/', views.signup_view, name='signup'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    #path('signup/', views.signup_view, name='signup'),
    path('signin/', views.signin_view, name='signin'),
    path('signout/', views.signout_view, name='signout'),
    #path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    
    # Employee URLs
    path('', views.employee_dashboard, name='employee_dashboard'),
    path('employee/profile/', views.employee_profile, name='employee_profile'),
    path('employee/attendance/', views.attendance_view, name='attendance_view'),
    path('employee/attendance/checkin/', views.attendance_checkin, name='attendance_checkin'),
    path('employee/attendance/checkout/', views.attendance_checkout, name='attendance_checkout'),
    path('employee/leave/create/', views.leave_request_create, name='leave_request_create'),
    path('employee/leave/', views.leave_request_list, name='leave_request_list'),
    path('employee/payroll/', views.payroll_view, name='payroll_view'),
    
    # Admin URLs
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/employees/', views.admin_employee_list, name='admin_employee_list'),
    path('admin/employees/<int:employee_id>/edit/', views.admin_employee_edit, name='admin_employee_edit'),
    path('admin/attendance/', views.admin_attendance_records, name='admin_attendance_records'),
    path('admin/leave/', views.admin_leave_approvals, name='admin_leave_approvals'),
    path('admin/leave/<int:leave_id>/<str:action>/', views.admin_leave_action, name='admin_leave_action'),
    path('admin/salary/', views.admin_salary_management, name='admin_salary_management'),
    path('admin/salary/<int:employee_id>/update/', views.admin_salary_update, name='admin_salary_update'),
]
