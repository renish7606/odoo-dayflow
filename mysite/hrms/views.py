from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q, Count
from datetime import datetime, timedelta
from .models import CustomUser, Profile, Attendance, LeaveRequest, Payroll
from .forms import SignUpForm, SignInForm, ProfileUpdateForm, AdminProfileUpdateForm, LeaveRequestForm
#-------------------------------------
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from .forms import SignUpForm
from .models import CustomUser


# ============== Helper Functions ==============

def is_admin(user):
    """Check if user is admin/HR officer"""
    return user.is_authenticated and user.role == 'ADMIN'


def is_employee(user):
    """Check if user is employee"""
    return user.is_authenticated and user.role == 'EMPLOYEE'


# ============== Authentication Views ==============

# def signup_view(request):
#     """User registration with email verification"""
#     if request.user.is_authenticated:
#         return redirect('employee_dashboard' if request.user.role == 'EMPLOYEE' else 'admin_dashboard')
    
#     if request.method == 'POST':
#         form = SignUpForm(request.POST)
#         if form.is_valid():
#             user = form.save(commit=False)
#             user.is_active = True  # User can login, but email not verified
#             user.save()
            
#             # Generate verification token
#             token = user.generate_verification_token()
            
#             # Create profile and default payroll
#             # Profile.objects.create(
#             #     user=user,
#             #     designation='Not Assigned',
#             #     department='Not Assigned'
#             # )
#             # Payroll.objects.create(
#             #     user=user,
#             #     basic_salary=0.00
#             # )
#             # Profile create safely
#             profile, created = Profile.objects.get_or_create(
#                 user=user,
#                 defaults={
#                     'designation': 'Not Assigned',
#                     'department': 'Not Assigned',
#                 }
#             )

#             # Payroll create safely
#             payroll, created = Payroll.objects.get_or_create(
#                 user=user,
#                 defaults={'basic_salary': 0.0}
#             )

#             # Send verification email
#             verification_url = request.build_absolute_uri(
#                 reverse('verify_email', kwargs={'token': token})
#             )
#             send_mail(
#                 subject='Verify your Dayflow account',
#                 message=f'Hello {user.first_name},\n\nPlease click the link below to verify your email:\n{verification_url}\n\nThank you!',
#                 from_email='noreply@dayflow.com',
#                 recipient_list=[user.email],
#                 fail_silently=False,
#             )
            
#             messages.success(request, 'Account created successfully! Please check your email to verify your account.')
#             return redirect('signin')
#     else:
#         form = SignUpForm()
    
#     return render(request, 'hrms/auth/signup.html', {'form': form})


def signup_view(request):
    """User registration with email verification, safe Profile and Payroll creation"""
    if request.user.is_authenticated:
        return redirect('employee_dashboard' if request.user.role == 'EMPLOYEE' else 'admin_dashboard')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Save user as inactive until email verification
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            # Create Profile safely (avoid UNIQUE constraint error)
            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults={
                    'designation': 'Not Assigned',
                    'department': 'Not Assigned',
                }
            )

            # Create Payroll safely
            payroll, created = Payroll.objects.get_or_create(
                user=user,
                defaults={'basic_salary': 0.0}
            )

            # Generate email verification token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            current_site = get_current_site(request)

            # Build verification URL
            verification_url = f"http://{current_site.domain}{reverse('activate', kwargs={'uidb64': uid, 'token': token})}"

            # Send verification email
            mail_subject = 'Activate your Dayflow HRMS Account'
            message = f"""
Hello {user.first_name},

Thank you for registering at Dayflow HRMS!

Please click the link below to activate your account:

{verification_url}

If you did not register, please ignore this email.
"""
            email = EmailMessage(mail_subject, message, to=[user.email])
            email.send(fail_silently=False)

            messages.success(request, 'Account created successfully! Please check your email to activate your account.')
            return redirect('signin')
    else:
        form = SignUpForm()
    
    return render(request, 'hrms/auth/signup.html', {'form': form})

def verify_email(request, token):
    """Verify user email"""
    try:
        user = CustomUser.objects.get(verification_token=token)
        user.email_verified = True
        user.verification_token = ''
        user.save()
        messages.success(request, 'Email verified successfully! You can now sign in.')
    except CustomUser.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
    
    return redirect('signin')

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.email_verified = True
        user.save()
        messages.success(request, 'Your account is activated! You can now sign in.')
        return redirect('signin')
    else:
        messages.error(request, 'Activation link is invalid or expired.')
        return render(request, 'hrms/activation_failed.html')

def signin_view(request):
    """User sign-in with role-based redirection"""
    if request.user.is_authenticated:
        return redirect('employee_dashboard' if request.user.role == 'EMPLOYEE' else 'admin_dashboard')
    
    if request.method == 'POST':
        form = SignInForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Redirect based on role
            if user.role == 'ADMIN':
                return redirect('admin_dashboard')
            else:
                return redirect('employee_dashboard')
    else:
        form = SignInForm()
    
    return render(request, 'hrms/auth/signin.html', {'form': form})


@login_required
def signout_view(request):
    """User sign-out"""
    logout(request)
    messages.success(request, 'You have been signed out successfully.')
    return redirect('signin')


# ============== Employee Views ==============

@login_required
@user_passes_test(is_employee, login_url='admin_dashboard')
def employee_dashboard(request):
    """Employee dashboard with quick access cards"""
    user = request.user
    today = timezone.now().date()
    
    # Get today's attendance
    today_attendance = Attendance.objects.filter(user=user, date=today).first()
    
    # Get recent leave requests
    recent_leaves = LeaveRequest.objects.filter(user=user)[:5]
    
    # Get latest payroll
    latest_payroll = Payroll.objects.filter(user=user).first()
    
    context = {
        'user': user,
        'today_attendance': today_attendance,
        'recent_leaves': recent_leaves,
        'latest_payroll': latest_payroll,
    }
    
    return render(request, 'hrms/employee/dashboard.html', context)


@login_required
@user_passes_test(is_employee, login_url='admin_dashboard')
def employee_profile(request):
    """Employee profile view and edit"""
    profile = request.user.profile
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('employee_profile')
    else:
        form = ProfileUpdateForm(instance=profile)
    
    # Get latest payroll
    latest_payroll = Payroll.objects.filter(user=request.user).first()
    
    context = {
        'form': form,
        'profile': profile,
        'latest_payroll': latest_payroll,
    }
    
    return render(request, 'hrms/employee/profile.html', context)


@login_required
@user_passes_test(is_employee, login_url='admin_dashboard')
def attendance_view(request):
    """Attendance view with check-in/out and weekly summary"""
    user = request.user
    today = timezone.now().date()
    
    # Get or create today's attendance
    today_attendance, created = Attendance.objects.get_or_create(
        user=user,
        date=today
    )
    
    # Get this week's attendance
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    weekly_attendance = Attendance.objects.filter(
        user=user,
        date__range=[week_start, week_end]
    ).order_by('date')
    
    context = {
        'today_attendance': today_attendance,
        'weekly_attendance': weekly_attendance,
        'week_start': week_start,
        'week_end': week_end,
    }
    
    return render(request, 'hrms/employee/attendance.html', context)


@login_required
@user_passes_test(is_employee, login_url='admin_dashboard')
def attendance_checkin(request):
    """Check-in attendance"""
    if request.method == 'POST':
        user = request.user
        today = timezone.now().date()
        
        attendance, created = Attendance.objects.get_or_create(
            user=user,
            date=today
        )
        
        if attendance.check_in_time:
            messages.warning(request, 'You have already checked in today.')
        else:
            attendance.check_in_time = timezone.now()
            attendance.status = 'PRESENT'
            attendance.save()
            messages.success(request, f'Checked in successfully at {attendance.check_in_time.strftime("%I:%M %p")}')
    
    return redirect('attendance_view')


@login_required
@user_passes_test(is_employee, login_url='admin_dashboard')
def attendance_checkout(request):
    """Check-out attendance"""
    if request.method == 'POST':
        user = request.user
        today = timezone.now().date()
        
        try:
            attendance = Attendance.objects.get(user=user, date=today)
            
            if not attendance.check_in_time:
                messages.error(request, 'Please check in first.')
            elif attendance.check_out_time:
                messages.warning(request, 'You have already checked out today.')
            else:
                attendance.check_out_time = timezone.now()
                attendance.calculate_total_hours()
                messages.success(request, f'Checked out successfully at {attendance.check_out_time.strftime("%I:%M %p")}. Total hours: {attendance.total_hours}')
        except Attendance.DoesNotExist:
            messages.error(request, 'Please check in first.')
    
    return redirect('attendance_view')


@login_required
@user_passes_test(is_employee, login_url='admin_dashboard')
def leave_request_create(request):
    """Create leave request"""
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave_request = form.save(commit=False)
            leave_request.user = request.user
            leave_request.save()
            messages.success(request, 'Leave request submitted successfully!')
            return redirect('leave_request_list')
    else:
        form = LeaveRequestForm()
    
    return render(request, 'hrms/employee/leave_request_create.html', {'form': form})


@login_required
@user_passes_test(is_employee, login_url='admin_dashboard')
def leave_request_list(request):
    """View all leave requests"""
    leave_requests = LeaveRequest.objects.filter(user=request.user)
    
    context = {
        'leave_requests': leave_requests,
    }
    
    return render(request, 'hrms/employee/leave_request_list.html', context)


@login_required
@user_passes_test(is_employee, login_url='admin_dashboard')
def payroll_view(request):
    """View payroll details (read-only)"""
    payrolls = Payroll.objects.filter(user=request.user)
    latest_payroll = payrolls.first()
    
    context = {
        'payrolls': payrolls,
        'latest_payroll': latest_payroll,
    }
    
    return render(request, 'hrms/employee/payroll.html', context)


# ============== Admin Views ==============

@login_required
@user_passes_test(is_admin, login_url='employee_dashboard')
def admin_dashboard(request):
    """Admin dashboard with overview statistics"""
    today = timezone.now().date()
    
    # Statistics
    total_employees = CustomUser.objects.filter(role='EMPLOYEE').count()
    present_today = Attendance.objects.filter(date=today, status='PRESENT').count()
    pending_leaves = LeaveRequest.objects.filter(status='PENDING').count()
    
    # Recent leave requests
    recent_leave_requests = LeaveRequest.objects.all()[:10]
    
    # Today's attendance summary
    today_attendance = Attendance.objects.filter(date=today).select_related('user')
    
    context = {
        'total_employees': total_employees,
        'present_today': present_today,
        'pending_leaves': pending_leaves,
        'recent_leave_requests': recent_leave_requests,
        'today_attendance': today_attendance,
    }
    
    return render(request, 'hrms/admin/dashboard.html', context)


@login_required
@user_passes_test(is_admin, login_url='employee_dashboard')
def admin_employee_list(request):
    """List all employees with search"""
    search_query = request.GET.get('search', '')
    employees = CustomUser.objects.filter(role='EMPLOYEE')
    
    if search_query:
        employees = employees.filter(
            Q(employee_id__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    context = {
        'employees': employees,
        'search_query': search_query,
    }
    
    return render(request, 'hrms/admin/employee_list.html', context)


@login_required
@user_passes_test(is_admin, login_url='employee_dashboard')
def admin_employee_edit(request, employee_id):
    """Edit employee profile (full access)"""
    employee = get_object_or_404(CustomUser, id=employee_id)
    profile = employee.profile
    
    if request.method == 'POST':
        form = AdminProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, f'Profile for {employee.get_full_name()} updated successfully!')
            return redirect('admin_employee_list')
    else:
        form = AdminProfileUpdateForm(instance=profile)
    
    context = {
        'form': form,
        'employee': employee,
        'profile': profile,
    }
    
    return render(request, 'hrms/admin/employee_edit.html', context)


@login_required
@user_passes_test(is_admin, login_url='employee_dashboard')
def admin_attendance_records(request):
    """View all attendance records"""
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    attendance_records = Attendance.objects.all().select_related('user')
    
    if date_from:
        attendance_records = attendance_records.filter(date__gte=date_from)
    if date_to:
        attendance_records = attendance_records.filter(date__lte=date_to)
    
    context = {
        'attendance_records': attendance_records,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'hrms/admin/attendance_records.html', context)


@login_required
@user_passes_test(is_admin, login_url='employee_dashboard')
def admin_leave_approvals(request):
    """View and approve/reject leave requests"""
    status_filter = request.GET.get('status', 'PENDING')
    
    leave_requests = LeaveRequest.objects.all().select_related('user')
    
    if status_filter:
        leave_requests = leave_requests.filter(status=status_filter)
    
    context = {
        'leave_requests': leave_requests,
        'status_filter': status_filter,
    }
    
    return render(request, 'hrms/admin/leave_approvals.html', context)


@login_required
@user_passes_test(is_admin, login_url='employee_dashboard')
def admin_leave_action(request, leave_id, action):
    """Approve or reject leave request"""
    leave_request = get_object_or_404(LeaveRequest, id=leave_id)
    
    if request.method == 'POST':
        comment = request.POST.get('comment', '')
        
        if action == 'approve':
            leave_request.status = 'APPROVED'
            leave_request.approved_by = request.user
            leave_request.admin_comment = comment
            leave_request.save()
            messages.success(request, f'Leave request for {leave_request.user.get_full_name()} approved.')
        elif action == 'reject':
            leave_request.status = 'REJECTED'
            leave_request.approved_by = request.user
            leave_request.admin_comment = comment
            leave_request.save()
            messages.success(request, f'Leave request for {leave_request.user.get_full_name()} rejected.')
    
    return redirect('admin_leave_approvals')


@login_required
@user_passes_test(is_admin, login_url='employee_dashboard')
def admin_salary_management(request):
    """Manage employee salaries"""
    employee_id = request.GET.get('employee')
    payrolls = Payroll.objects.all().select_related('user')
    employees = CustomUser.objects.filter(role='EMPLOYEE')
    
    if employee_id:
        payrolls = payrolls.filter(user_id=employee_id)
    
    context = {
        'payrolls': payrolls,
        'employees': employees,
        'selected_employee': employee_id,
    }
    
    return render(request, 'hrms/admin/salary_management.html', context)


@login_required
@user_passes_test(is_admin, login_url='employee_dashboard')
def admin_salary_update(request, employee_id):
    """Update employee salary"""
    employee = get_object_or_404(CustomUser, id=employee_id)
    latest_payroll = Payroll.objects.filter(user=employee).first()
    
    if request.method == 'POST':
        # Create new payroll record
        payroll = Payroll.objects.create(
            user=employee,
            basic_salary=request.POST.get('basic_salary', 0),
            house_rent_allowance=request.POST.get('hra', 0),
            transport_allowance=request.POST.get('transport', 0),
            medical_allowance=request.POST.get('medical', 0),
            other_allowances=request.POST.get('other_allowances', 0),
            provident_fund=request.POST.get('pf', 0),
            professional_tax=request.POST.get('professional_tax', 0),
            income_tax=request.POST.get('income_tax', 0),
            other_deductions=request.POST.get('other_deductions', 0),
        )
        messages.success(request, f'Salary updated for {employee.get_full_name()}')
        return redirect('admin_salary_management')
    
    context = {
        'employee': employee,
        'latest_payroll': latest_payroll,
    }
    
    return render(request, 'hrms/admin/salary_update.html', context)

#email verification 
# def signup(request):
#     if request.method == 'POST':
#         form = SignUpForm(request.POST)
#         if form.is_valid():
#             user = form.save(commit=False)
#             user.is_active = False  # Inactive until email verification
#             user.save()

#             # Generate token for verification
#             token = default_token_generator.make_token(user)
#             uid = urlsafe_base64_encode(force_bytes(user.pk))
#             current_site = get_current_site(request)

#             mail_subject = 'Activate your Dayflow HRMS Account'
#             message = render_to_string('hrms/activate_account.html', {
#                 'user': user,
#                 'domain': current_site.domain,
#                 'uid': uid,
#                 'token': token,
#             })
#             email = EmailMessage(mail_subject, message, to=[user.email])
#             email.send()

#             messages.success(request, 'Account created! Check your email to activate your account.')
#             return redirect('hrms:signup')
#     else:
#         form = SignUpForm()

#     return render(request, 'hrms/auth/signup.html', {'form': form})


# def activate(request, uidb64, token):
#     try:
#         uid = force_str(urlsafe_base64_decode(uidb64))
#         user = CustomUser.objects.get(pk=uid)
#     except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
#         user = None

#     if user and default_token_generator.check_token(user, token):
#         user.is_active = True
#         user.email_verified = True
#         user.save()
#         messages.success(request, 'Your account is activated! You can now log in.')
#         return redirect('signin')
#     else:
#         messages.error(request, 'Activation link is invalid or expired!')
#         return render(request, 'hrms/activation_failed.html')
# Generate token
