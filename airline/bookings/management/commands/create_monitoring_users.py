from django.core.management.base import BaseCommand
from bookings.models import MonitoringUser

class Command(BaseCommand):
    help = 'Create monitoring users for airline admins'

    def handle(self, *args, **options):
        airlines = [
            ('AI', 'Air India'),
            ('SG', 'SpiceJet'),
            ('6E', 'IndiGo'),
            ('UK', 'Vistara'),
            ('G8', 'GoAir'),
            ('I5', 'AirAsia India'),
            ('9W', 'Jet Airways'),
            ('DN', 'Alliance Air'),
            ('S2', 'JetLite'),
            ('IT', 'Kingfisher'),
        ]
        
        created_count = 0
        
        for code, name in airlines:
            username = f"{code.lower()}_admin"
            
            if not MonitoringUser.objects.filter(username=username, airline_code=code).exists():
                user = MonitoringUser.objects.create(
                    username=username,
                    airline_code=code,
                    first_name=name.split()[0],
                    last_name='Admin',
                    email=f"{username}@{name.lower().replace(' ', '')}.com",
                    is_active=True,
                    created_by='system'
                )
                user.set_password('admin123')  # Default password
                user.save()
                
                created_count += 1
                self.stdout.write(f"Created monitoring user: {username} (Password: admin123)")
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} monitoring users')
        )