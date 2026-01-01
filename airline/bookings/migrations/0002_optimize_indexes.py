from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('bookings', '0001_initial'),
    ]

    operations = [
        # Add indexes for common queries
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_booking_state_hold ON airline_bookings(state, seat_hold_until) WHERE state = 'SEAT_HELD';",
            reverse_sql="DROP INDEX IF EXISTS idx_booking_state_hold;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_seat_flight_booked ON airline_seats(flight_id, is_booked);",
            reverse_sql="DROP INDEX IF EXISTS idx_seat_flight_booked;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_booking_user_state ON airline_bookings(created_by_id, state);",
            reverse_sql="DROP INDEX IF EXISTS idx_booking_user_state;"
        ),
    ]