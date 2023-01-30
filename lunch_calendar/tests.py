# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=too-many-arguments

import unittest
from unittest.mock import MagicMock, Mock, call, patch

from lunch_calendar.app import (
    add_calendar_events,
    get_calendar,
    get_calendar_name,
    get_month,
    parse_calendar,
    write_calendar,
)


class TestStringMethods(unittest.TestCase):
    def setUp(self) -> None:
        self.calendar_name = "sre-jan-23"
        self.school = "sre"
        self.month = 1
        self.year = 2023
        self.params = (self.school, self.month, self.year)

    def test_get_month(self):
        self.assertEqual(get_month(1), "jan")
        self.assertEqual(get_month(12), "dec")

    @patch("lunch_calendar.app.get_month")
    def test_get_calendar_name(self, mock_get_month):
        mock_get_month.return_value = "jan"
        returned_response = get_calendar_name(*self.params)
        self.assertEqual(self.calendar_name, returned_response)

    @patch("lunch_calendar.app.get_calendar_name")
    @patch("lunch_calendar.app.requests")
    def test_get_calendar(self, mock_requests, mock_get_calendar_name):
        example_calendar = "<html>Calendar</html>"
        example_calendar_url = f"http://www.belchertownps.org/sites/default/files/menus/{self.calendar_name}.html"
        mock_get_calendar_name.return_value = self.calendar_name
        mock_requests.get.return_value.content = example_calendar
        self.assertEqual(get_calendar(*self.params), example_calendar)
        mock_requests.get.assert_called_once_with(example_calendar_url, timeout=20)

    def test_parse_calendar(self):
        date_text = "3"
        date_element = Mock(text=date_text)
        meal_text = "Meal Title \n Meal Items \n"
        meal_element = Mock(text=meal_text)
        expected_meals = {date_text: meal_element}
        days = [Mock(find=Mock(side_effect=[date_element, meal_element]))]
        mock_soup = Mock(find_all=Mock(return_value=days))
        self.assertEqual(expected_meals, parse_calendar(mock_soup))

    @patch("lunch_calendar.app.Event")
    def test_add_calendar_events(self, mock_event):
        mock_event_instance = Mock(add=Mock())
        mock_event.return_value = mock_event_instance
        mock_calendar = MagicMock()
        date_text = "3"
        meal_text = ["Meal Title", "Meal Items"]
        meal_lines = [Mock(text=meal_text[0]), Mock(text=meal_text[1])]

        meal_element = Mock(find_all=Mock(return_value=meal_lines))
        example_meals = {date_text: meal_element}
        add_calendar_events(mock_calendar, example_meals, *self.params)
        self.assertEqual(len(mock_event_instance.add.mock_calls), 4)
        mock_calendar.add_component(mock_event_instance)

    @patch("lunch_calendar.app.Response")
    @patch("lunch_calendar.app.add_calendar_events")
    @patch("lunch_calendar.app.parse_calendar")
    @patch("lunch_calendar.app.BeautifulSoup")
    @patch("lunch_calendar.app.get_calendar")
    @patch("lunch_calendar.app.Calendar")
    def test_write_calendar(
        self,
        mock_calendar,
        mock_get_calendar,
        mock_beautiful_soup,
        mock_parse_calendar,
        mock_add_calendar_events,
        mock_response,
    ):
        example_path = "sre.ics"
        mock_response_instance = Mock(headers={})
        mock_response.return_value = mock_response_instance
        mock_calendar_instance = MagicMock()
        mock_calendar.return_value = mock_calendar_instance
        self.assertEqual(mock_response_instance, write_calendar(example_path))
        mock_get_calendar.assert_has_calls(
            [
                call("sre", 1, 2023),
                call().__bool__(),
                call("sre", 2, 2023),
                call().__bool__(),
            ]
        )
        mock_beautiful_soup.assert_called()
        mock_parse_calendar.assert_called()
        mock_add_calendar_events.assert_called()


if __name__ == "__main__":
    unittest.main()
