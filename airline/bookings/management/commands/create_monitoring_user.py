from django.core.management.base import BaseCommand
from bookings.models import MonitoringUser

class Command(BaseCommand):
    help = 'Create a monitoring user'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username for monitoring user', default='admin')
        parser.add_argument('--password', type=str, help='Password for monitoring user', default='admin123')
        parser.add_argument('--first_name', type=str, help='First name', default='Admin')
        parser.add_argument('--last_name', type=str, help='Last name', default='User')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']

        # Check if user already exists
        if MonitoringUser.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Monitoring user "{username}" already exists')
            )
            return

        # Create monitoring user
        user = MonitoringUser.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            actual_password=password
        )
        user.set_password(password)
        user.save()

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created monitoring user "{username}" with password "{password}"')
        )