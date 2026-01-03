from django.core.management.base import BaseCommand
from hrms.models import Payroll
from django.db.models import Count


class Command(BaseCommand):
    help = 'Remove duplicate payroll records, keeping only the most recent one per user/effective_date'

    def handle(self, *args, **options):
        # Find duplicate payroll records (same user and effective_date)
        duplicates = (
            Payroll.objects.values('user', 'effective_date')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )
        
        total_deleted = 0
        
        for dup in duplicates:
            # Get all payroll records for this user/effective_date combination
            payrolls = Payroll.objects.filter(
                user_id=dup['user'],
                effective_date=dup['effective_date']
            ).order_by('-created_at')  # Most recent first
            
            # Delete all except the most recent one
            to_delete = payrolls[1:]  # Skip the first (most recent)
            count = len(to_delete)
            
            for payroll in to_delete:
                self.stdout.write(
                    f"Deleting payroll ID {payroll.id} for user {payroll.user.employee_id} "
                    f"(effective_date: {payroll.effective_date}, created: {payroll.created_at})"
                )
                payroll.delete()
                total_deleted += 1
        
        if total_deleted > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {total_deleted} duplicate payroll record(s)'
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS('No duplicate payroll records found'))
