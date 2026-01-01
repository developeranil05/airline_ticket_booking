@echo off
echo Setting up Airline Booking System...

REM Install dependencies
pip install Django djangorestframework psycopg2-binary

REM Create migrations
python manage.py makemigrations bookings

REM Apply migrations
python manage.py migrate

REM Create superuser (you'll be prompted for username/password)
python manage.py createsuperuser

REM Seed sample data
python manage.py seed_data

echo Setup complete!
echo.
echo Next steps:
echo 1. Run: python manage.py runserver
echo 2. Visit: http://127.0.0.1:8000/
echo 3. Admin: http://127.0.0.1:8000/admin/
pause