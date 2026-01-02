from django.core.management.base import BaseCommand
from bookings.models import AdminUser, MonitoringUser

class Command(BaseCommand):
    help = 'Create admin users'

    def handle(self, *args, **options):
        # Show all monitoring users
        all_monitoring = MonitoringUser.objects.all()
        self.stdout.write(f'All monitoring users ({all_monitoring.count()}):')
        for user in all_monitoring:
            self.stdout.write(f'  - {user.username}')
        
        # Create admin users for all airlines
        AdminUser.objects.all().delete()
        
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
            ('IT', 'Kingfisher')
        ]
        
        for code, name in airlines:
            admin_name = f'{name} Admin'
            # Generate phone number based on airline code
            phone_base = ord(code[0]) * 100 + ord(code[1] if len(code) > 1 else 'A')
            phone_number = f'+91-{9000 + phone_base % 1000}-{phone_base % 10000:04d}'
            # Generate actual password (not hashed for display)
            actual_password = f'{code.lower()}admin123'
            
            admin_user = AdminUser.objects.create(
                admin_name=admin_name,
                airline_code=code,
                airline_name=name,
                email=f'{code.lower()}_admin@{name.lower().replace(" ", "")}.com',
                phone_number=phone_number,
                is_active=True
            )
            admin_user.set_password(actual_password)
            admin_user.save()
            
            # Store actual password for monitoring display
            admin_user.actual_password = actual_password
            admin_user.save()
            
            self.stdout.write(f'Created: {admin_name} ({code}) - {phone_number} - Password: {actual_password}')
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(airlines)} admin users'))