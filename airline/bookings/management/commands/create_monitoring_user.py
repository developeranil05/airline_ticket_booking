from django.core.management.base import BaseCommand
from bookings.models import MonitoringUser

class Command(BaseCommand):
    help = 'Create monitoring user anmol'

    def handle(self, *args, **options):
        # Create anmol user
        user, created = MonitoringUser.objects.get_or_create(
            username='anmol',
            defaults={
                'first_name': 'Anmol',
                'last_name': 'User',
                'is_active': True,
            }
        )
        
        if created:
            user.set_password('anmol')
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created monitoring user: anmol')
            )
        else:
            # Update password if user exists
            user.set_password('anmol')
            user.save()
            self.stdout.write(
                self.style.WARNING(f'Updated existing monitoring user: anmol')
            )