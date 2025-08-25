# stgospel
Orthodox calendar. Group management. Reading in groups. 

# Installation

## Install Calendar from https://calendar.rop.ru
1. create dirs:
gospel/calendar/<year>/src
gospel/calendar/<year>/script
gospel/calendar/<year>/json
2. python manage.py fetch_calendar
3. python manage.py fetch_trapeza
4. python manage.py parse_calendar


## Database setup
´´´sql
CREATE USER 'gospel'@'localhost' IDENTIFIED BY 'PassWORD';

CREATE SCHEMA `stgospel` DEFAULT CHARACTER SET utf8mb4 ;

GRANT ALL PRIVILEGES ON stgospel.* TO 'gospel'@'localhost';
´´´

## Import Bible to DB from txt
1. python manage.py txt2db
2. python manage.py prim2db
3. python manage.py psaltir2db
4. python manage.py make_orders_patch

