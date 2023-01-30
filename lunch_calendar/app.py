"""A basic application to parse a calendar and serve an ICS file."""

import calendar
import logging
import os
from datetime import datetime
from typing import Optional

import pytz
import requests
from bs4 import BeautifulSoup, Tag
from flask import Flask, Response
from flask_caching import Cache
from icalendar import Calendar, Event  # type: ignore

app = Flask(__name__)

CACHE_TIMEOUT = int(os.getenv("CACHE_TIMEOUT", "28800"))
app.config["CACHE_TYPE"] = "FileSystemCache"
app.config["CACHE_DIR"] = "./cache"  # path to your server cache folder
app.config["CACHE_THRESHOLD"] = 1000

cache = Cache(app)
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    filename="example.log", encoding="utf-8", level=logging.getLevelName(log_level)
)

calendar_root = os.getenv(
    "CALENDAR_URL", "http://www.belchertownps.org/sites/default/files/menus"
).rstrip("/")


def get_month(month_number: int) -> str:
    """
    Converts an integer to a three letter month.
    :param month_number: An integer for the month.
    :return: A string for the month.
    """
    return [
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    ][month_number - 1]


def get_calendar_name(school: str, month: int, year: int) -> str:
    """
    :param year: An integer representing the year.
    :param month: An integer representing the month
    :param school: Three character school code (i.e. css, sre...)
    :return: String for this months calendar (css-jan-23)
    """
    return f"{school}-{get_month(month)}-{str(year)[2:]}"


def get_calendar(school: str, month: int, year: int) -> Optional[str]:
    """
    :param year: An integer representing the year.
    :param month: An integer representing the month
    :param school: Three character school code (i.e. css, sre...)
    :return: HTML response with the calendar.
    """
    calendar_url = f"{calendar_root}/{get_calendar_name(school, month, year)}.html"
    try:
        response = requests.get(calendar_url, timeout=20)
        response.raise_for_status()
        return str(response.content)
    except requests.RequestException:
        logging.error("Could not get calendar from %s", calendar_url)
    return None


def parse_calendar(soup: BeautifulSoup) -> dict[str, Tag]:
    """

    :param soup: A beautiful soup object from the HTML calendar.
    :return: A dictionary of days and meals.
    """

    days = soup.find_all(class_="day")
    meals: dict[str, Tag] = {}
    if not days:
        return meals
    for day in days:
        date_element = day.find(class_="dateNumber")
        meal_element = day.find(class_="meal-desc")
        if date_element and meal_element:
            meals[date_element.text.replace("\\n", "").strip()] = meal_element
    return meals


def add_calendar_events(
    cal: Calendar, meals: dict[str, Tag], school: str, month: int, year: int
):
    """

    :param cal: An icalendar object.
    :param meals:  The meals represented as a dict of days/meals.
    :param school: The abbreviation for the school.
    :param month: The month as an integer.
    :param year: The year as an integer.
    :return: None.
    """
    for day, meal in meals.items():
        if not meal:
            continue
        meal_lines = meal.find_all("span")
        event = Event()
        event.add("uid", f"{get_calendar_name(school, month, year)}-{day}")
        event.add("summary", meal_lines[0].text.strip("\\n").strip())
        event.add(
            "description",
            "\n".join([line.text.strip("\\n").strip() for line in meal_lines]),
        )
        event.add("dtstart", datetime(year, month, int(day), tzinfo=pytz.utc).date())
        cal.add_component(event)


@app.route("/<calendar_path>")
@cache.cached(timeout=CACHE_TIMEOUT)
def write_calendar(calendar_path):
    """
    :param calendar_path: A string parsed from the url for the school (i.e. sre.ics)
    :return: An icalendar response.
    """
    school, _ = os.path.splitext(calendar_path)
    cal = Calendar()
    cal.add("version", "2.0")
    cal.add("method", "PUBLISH")
    title = None
    today = datetime.today()
    # pylint: disable=protected-access
    for year, month in [
        (today.year, today.month),
        calendar._nextmonth(today.year, today.month),
    ]:
        meal_calendar = get_calendar(school, month, year)
        if not meal_calendar:
            continue
        soup = BeautifulSoup(meal_calendar, "html.parser")
        meals = parse_calendar(soup)
        add_calendar_events(cal, meals, school, month, year)
        if not title:
            title = soup.find(id="reportHeadingHeader").text.replace("\\n", "").strip()
            cal.add("prodid", f"-//{title}//")
    resp = Response(cal.to_ical())

    resp.headers["content-type"] = "text/calendar"
    return resp


if __name__ == "__main__":
    app.run()
