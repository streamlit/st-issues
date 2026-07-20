from __future__ import annotations

from datetime import date

type DateInputValue = date | tuple[()] | tuple[date] | tuple[date, date]


def normalize_date_range(date_input_value: DateInputValue) -> tuple[date | None, date | None]:
    """Normalize a Streamlit date_input value into a start/end tuple."""
    if isinstance(date_input_value, date):
        return date_input_value, date_input_value
    dates: tuple[date, ...] = date_input_value
    if len(dates) == 2:
        return dates[0], dates[1]
    if len(dates) == 1:
        return dates[0], None
    return None, None
