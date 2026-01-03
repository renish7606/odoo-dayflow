from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from django.http import HttpResponse
from datetime import datetime, timedelta
from .models import CustomUser, Profile, Attendance, LeaveRequest, Payroll
from .forms import SignUpForm, SignInForm, ProfileUpdateForm, AdminProfileUpdateForm, LeaveRequestForm
from .utils import generate_salary_slip_pdf


# ============== Helper Functions ==============

def is_admin(user):
    """Check if user is admin/HR officer"""
    return user.is_authenticated and user.role == 'ADMIN'


def is_employee(user):
    """Check if user is employee"""
    return user.is_authenticated and user.role == 'EMPLOYEE'


# ============== Authentication Views ==============

def signup_view(request):
    """User registration with email verification"""
    if request.user.is_authenticated:
        return redirect('employee_dashboard' if request.user.role == 'EMPLOYEE' else 'admin_dashboard')
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True  # User can login, but email not verified
            user.save()
            
            # Generate verification token
            token = user.generate_verification_token()
            
            # Note: Profile and Payroll are automatically created by signals.py
            
            # Send verification email
            verification_url = request.build_absolute_uri(
                reverse('verify_email', kwargs={'token': token})
            )
            send_mail(
                subject='Verify your Dayflow account',
                message=f'Hello {user.first_name},\n\nPlease click the link below to verify your email:\n{verification_url}\n\nThank you!',
                from_email='noreply@dayflow.com',
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            messages.success(request, 'Account created successfully! Please check your email to verify your account.')
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
        # Get effective date from POST or use today
        from django.utils import timezone
        effective_date = request.POST.get('effective_date', timezone.now().date())
        
        # Update existing payroll record with same effective date, or create new one
        payroll, created = Payroll.objects.update_or_create(
            user=employee,
            effective_date=effective_date,
            defaults={
                'basic_salary': request.POST.get('basic_salary', 0),
                'house_rent_allowance': request.POST.get('hra', 0),
                'transport_allowance': request.POST.get('transport', 0),
                'medical_allowance': request.POST.get('medical', 0),
                'other_allowances': request.POST.get('other_allowances', 0),
                'provident_fund': request.POST.get('pf', 0),
                'professional_tax': request.POST.get('professional_tax', 0),
                'income_tax': request.POST.get('income_tax', 0),
                'other_deductions': request.POST.get('other_deductions', 0),
            }
        )
        action = 'created' if created else 'updated'
        messages.success(request, f'Salary {action} for {employee.get_full_name()}')
        return redirect('admin_salary_management')
    
    context = {
        'employee': employee,
        'latest_payroll': latest_payroll,
    }
    
    return render(request, 'hrms/admin/salary_update.html', context)


# ============== Enhanced Payroll Views ==============

@login_required
@user_passes_test(is_employee, login_url='admin_dashboard')
def download_salary_slip(request, payroll_id):
    """Download salary slip as PDF"""
    payroll = get_object_or_404(Payroll, id=payroll_id, user=request.user)
    
    # Get month and year from query params or use current
    month = request.GET.get('month', timezone.now().month)
    year = request.GET.get('year', timezone.now().year)
    
    try:
        month = int(month)
        year = int(year)
    except (ValueError, TypeError):
        month = timezone.now().month
        year = timezone.now().year
    
    # Generate PDF
    pdf = generate_salary_slip_pdf(payroll, month, year)
    
    # Create HTTP response with PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f'salary_slip_{request.user.employee_id}_{year}_{month:02d}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
@user_passes_test(is_admin, login_url='employee_dashboard')
def admin_download_salary_slip(request, payroll_id):
    """Admin can download any employee's salary slip"""
    payroll = get_object_or_404(Payroll, id=payroll_id)
    
    # Get month and year from query params or use current
    month = request.GET.get('month', timezone.now().month)
    year = request.GET.get('year', timezone.now().year)
    
    try:
        month = int(month)
        year = int(year)
    except (ValueError, TypeError):
        month = timezone.now().month
        year = timezone.now().year
    
    # Generate PDF
    pdf = generate_salary_slip_pdf(payroll, month, year)
    
    # Create HTTP response with PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f'salary_slip_{payroll.user.employee_id}_{year}_{month:02d}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


# ============== Enhanced Attendance Views ==============

@login_required
@user_passes_test(is_employee, login_url='admin_dashboard')
def attendance_monthly_view(request):
    """View monthly attendance with aggregation"""
    user = request.user
    today = timezone.now().date()
    
    # Get month and year from query params or use current
    month = request.GET.get('month', today.month)
    year = request.GET.get('year', today.year)
    
    try:
        month = int(month)
        year = int(year)
    except (ValueError, TypeError):
        month = today.month
        year = today.year
    
    # Get month's attendance
    from calendar import monthrange
    _, last_day = monthrange(year, month)
    month_start = datetime(year, month, 1).date()
    month_end = datetime(year, month, last_day).date()
    
    monthly_attendance = Attendance.objects.filter(
        user=user,
        date__range=[month_start, month_end]
    ).order_by('date')
    
    # Calculate statistics
    present_count = monthly_attendance.filter(status='PRESENT').count()
    half_day_count = monthly_attendance.filter(status='HALF_DAY').count()
    absent_count = monthly_attendance.filter(status='ABSENT').count()
    total_hours = monthly_attendance.aggregate(Sum('total_hours'))['total_hours__sum'] or 0
    
    # Get approved leaves for this month
    approved_leaves = LeaveRequest.objects.filter(
        user=user,
        status='APPROVED',
        start_date__lte=month_end,
        end_date__gte=month_start
    )
    
    context = {
        'monthly_attendance': monthly_attendance,
        'month': month,
        'year': year,
        'month_name': datetime(year, month, 1).strftime('%B'),
        'present_count': present_count,
        'half_day_count': half_day_count,
        'absent_count': absent_count,
        'total_hours': total_hours,
        'approved_leaves': approved_leaves,
    }
    
    return render(request, 'hrms/employee/attendance_monthly.html', context)


@login_required
@user_passes_test(is_admin, login_url='employee_dashboard')
def admin_attendance_summary(request):
    """Admin view for attendance summary with aggregation"""
    today = timezone.now().date()
    
    # Get date range from query params
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    employee_id = request.GET.get('employee', '')
    
    # Default to current month if no dates provided
    if not date_from:
        date_from = today.replace(day=1)
    else:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
    
    if not date_to:
        from calendar import monthrange
        _, last_day = monthrange(today.year, today.month)
        date_to = today.replace(day=last_day)
    else:
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    # Get attendance records
    attendance_records = Attendance.objects.filter(
        date__range=[date_from, date_to]
    ).select_related('user')
    
    if employee_id:
        attendance_records = attendance_records.filter(user_id=employee_id)
    
    # Calculate aggregated statistics per employee
    employee_stats = attendance_records.values('user__id', 'user__employee_id', 'user__first_name', 'user__last_name').annotate(
        total_days=Count('id'),
        present_days=Count('id', filter=Q(status='PRESENT')),
        half_days=Count('id', filter=Q(status='HALF_DAY')),
        absent_days=Count('id', filter=Q(status='ABSENT')),
        total_hours=Sum('total_hours')
    )
    
    # Get all employees for filter
    employees = CustomUser.objects.filter(role='EMPLOYEE')
    
    context = {
        'attendance_records': attendance_records,
        'employee_stats': employee_stats,
        'employees': employees,
        'date_from': date_from,
        'date_to': date_to,
        'selected_employee': employee_id,
    }
    
    return render(request, 'hrms/admin/attendance_summary.html', context)


# ============== Helper Function for Leave Auto-Marking ==============

def mark_leave_attendance():
    """
    Auto-mark attendance as 'LEAVE' for approved leave requests.
    This should be called daily (e.g., via a cron job or management command).
    """
    today = timezone.now().date()
    
    # Get all approved leaves that cover today
    approved_leaves = LeaveRequest.objects.filter(
        status='APPROVED',
        start_date__lte=today,
        end_date__gte=today
    )
    
    for leave in approved_leaves:
        # Create or update attendance record
        attendance, created = Attendance.objects.get_or_create(
            user=leave.user,
            date=today,
            defaults={
                'status': 'ABSENT',  # Mark as absent initially
                'notes': f'On {leave.get_leave_type_display()} leave'
            }
        )
        
        # If no check-in, mark as leave
        if not attendance.check_in_time:
            attendance.status = 'ABSENT'
            attendance.notes = f'On {leave.get_leave_type_display()} leave'
            attendance.save()
    
    return len(approved_leaves)
