@echo off
cd /d c:\Users\HP\OneDrive\Desktop\Github_Projects\airline_ticket_booking
call env\Scripts\activate
cd airline
python manage.py runserver 8080
pause