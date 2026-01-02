# Run this in Django shell: python manage.py shell
from bookings.models import MonitoringUser

# Create monitoring user
user = MonitoringUser.objects.create(
    username='admin',
    first_name='Admin',
    last_name='User',
    is_active=True
)
user.set_password('admin123')
user.save()

print("Created monitoring user: admin / admin123")

# List all monitoring users
print("\nAll monitoring users:")
for u in MonitoringUser.objects.all():
    print(f"- {u.username} ({u.first_name} {u.last_name}) - Active: {u.is_active}")