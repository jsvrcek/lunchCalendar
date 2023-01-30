# Belchertown Public Schools Lunch Calendar Sync Tool

A simple python (flask) web application which can be used to parse a basic html page and serve out an ics file.

# Installation

```bash
pip install .
```
Then
```
FLASK_APP=<path_to_app>/app.py flask run -h <ip> -p <port>
```
OR
```
python lunch_calendar/app.py
```
Open browser and navigate to a school code for the desired calendar (i.e. http://localhost:5000/sre.ics).  The current and (if available) next months will be served in an ics file.


## Settings

Cache timeout should probably be kept to less than 24 hours, just so that updates can happen within a day.  That said, 
keeping the timeout very high will prevent needless requests from the html calendar, and will ensure calendars are loaded
instantly.

`CACHE_TIMEOUT` = A timeout in seconds to clear the cached ics lunch (default: 28800). 

`CALENDAR_URL` = The root url to get the calendar (default: http://www.belchertownps.org/sites/default/files/menus)

`LOG_LEVEL` = The log level (default: INFO)
