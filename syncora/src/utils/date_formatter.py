from dateutil import parser


def format_date(date: str) -> str:
    return parser.parse(date).strftime("%d/%m/%Y") if date else ""
