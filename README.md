# nldate

`nldate` is a small Python package for parsing common natural-language date
phrases into `datetime.date` objects.

```python
from datetime import date

from nldate import parse

parse("5 days before December 1st, 2025")
parse("two weeks from tomorrow", today=date(2025, 11, 20))
parse("next Tuesday", today=date(2025, 11, 20))
```

## Supported examples

- Absolute dates: `December 1st, 2025`, `1 Dec 25`, `2025-12-01`, `12/1/2025`
- Relative anchors: `today`, `tomorrow`, `yesterday`,
  `the day after tomorrow`, `the day before yesterday`
- Durations: `in 3 days`, `10 weeks ago`, `two weeks from tomorrow`,
  `1 year and 2 months after yesterday`
- Weekdays: `next Tuesday`, `last Friday`, `this Thursday`

## Development

```bash
uv run pytest
uv run mypy
uv run ruff check
```
