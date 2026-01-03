from django.core.management.base import BaseCommand
from hrms.models import CustomUser, Profile, Payroll


class Command(BaseCommand):
    help = 'Create missing Profile and Payroll records for existing users'

    def handle(self, *args, **options):
        users_fixed = 0
        
        for user in CustomUser.objects.all():
            # Create Profile if missing
            if not hasattr(user, 'profile'):
                Profile.objects.create(
                    user=user,
                    designation='Not Assigned',
                    department='Not Assigned'
                )
                self.stdout.write(self.style.SUCCESS(f'Created Profile for {user.username}'))
                users_fixed += 1
            
            # Create Payroll if missing
            if not Payroll.objects.filter(user=user).exists():
                Payroll.objects.create(
                    user=user,
                    basic_salary=0.00
                )
                self.stdout.write(self.style.SUCCESS(f'Created Payroll for {user.username}'))
        
        if users_fixed > 0:
            self.stdout.write(self.style.SUCCESS(f'\nFixed {users_fixed} users!'))
        else:
            self.stdout.write(self.style.SUCCESS('All users already have profiles!'))
