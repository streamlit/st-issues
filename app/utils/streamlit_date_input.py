from __future__ import annotations

from datetime import date

type DateInputValue = date | tuple[()] | tuple[date] | tuple[date, date]


def normalize_date_range(date_input_value: DateInputValue) -> tuple[date | None, date | None]:
    """Normalize a Streamlit date_input value into a start/end tuple."""
    match date_input_value:
        case (start_date, end_date):
            return start_date, end_date
        case (start_date,):
            return start_date, None
        case _ if isinstance(date_input_value, date):
            return date_input_value, date_input_value
        case _:
            return None, None
