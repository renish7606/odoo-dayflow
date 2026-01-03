from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
import secrets


class CustomUser(AbstractUser):
    """Custom user model with employee ID and role"""
    ROLE_CHOICES = [
        ('ADMIN', 'Admin/HR Officer'),
        ('EMPLOYEE', 'Employee'),
    ]
    
    employee_id = models.CharField(
        max_length=20, 
        unique=True,
        validators=[RegexValidator(
            regex=r'^EMP\d{4,6}$',
            message='Employee ID must be in format: EMP1234'
        )]
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='EMPLOYEE')
    email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.employee_id} - {self.get_full_name()}"
    
    def generate_verification_token(self):
        """Generate a unique verification token"""
        self.verification_token = secrets.token_urlsafe(32)
        self.save()
        return self.verification_token


class Profile(models.Model):
    """Employee profile with job and personal details"""
    EMPLOYMENT_TYPE_CHOICES = [
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('CONTRACT', 'Contract'),
        ('INTERN', 'Intern'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    designation = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    date_of_joining = models.DateField(default=timezone.now)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default='FULL_TIME')
    
    # Personal information (editable by employee)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    
    # Profile picture
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.employee_id} - {self.designation}"


class Attendance(models.Model):
    """Employee attendance tracking"""
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('HALF_DAY', 'Half Day'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.now)
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ABSENT')
    total_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendance Records'
    
    def __str__(self):
        return f"{self.user.employee_id} - {self.date} - {self.status}"
    
    def calculate_total_hours(self):
        """Calculate total hours worked"""
        if self.check_in_time and self.check_out_time:
            delta = self.check_out_time - self.check_in_time
            hours = delta.total_seconds() / 3600
            self.total_hours = round(hours, 2)
            
            # Set status based on hours
            if hours >= 8:
                self.status = 'PRESENT'
            elif hours >= 4:
                self.status = 'HALF_DAY'
            else:
                self.status = 'ABSENT'
            
            self.save()


class LeaveRequest(models.Model):
    """Employee leave request management"""
    LEAVE_TYPE_CHOICES = [
        ('PAID', 'Paid Leave'),
        ('SICK', 'Sick Leave'),
        ('UNPAID', 'Unpaid Leave'),
        ('CASUAL', 'Casual Leave'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=10, choices=LEAVE_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    remarks = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    admin_comment = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_leaves'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Leave Request'
        verbose_name_plural = 'Leave Requests'
    
    def __str__(self):
        return f"{self.user.employee_id} - {self.leave_type} ({self.start_date} to {self.end_date})"
    
    @property
    def total_days(self):
        """Calculate total leave days"""
        return (self.end_date - self.start_date).days + 1


class Payroll(models.Model):
    """Employee payroll and salary structure"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payrolls')
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Allowances (stored as JSON for flexibility)
    house_rent_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    transport_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    medical_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    other_allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Deductions
    provident_fund = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    professional_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    income_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    effective_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-effective_date']
        verbose_name = 'Payroll'
        verbose_name_plural = 'Payroll Records'
    
    def __str__(self):
        return f"{self.user.employee_id} - ₹{self.net_salary}"
    
    @property
    def gross_salary(self):
        """Calculate gross salary (basic + all allowances)"""
        return (
            self.basic_salary + 
            self.house_rent_allowance + 
            self.transport_allowance + 
            self.medical_allowance + 
            self.other_allowances
        )
    
    @property
    def total_deductions(self):
        """Calculate total deductions"""
        return (
            self.provident_fund + 
            self.professional_tax + 
            self.income_tax + 
            self.other_deductions
        )
    
    @property
    def net_salary(self):
        """Calculate net salary (gross - deductions)"""
        return self.gross_salary - self.total_deductions
