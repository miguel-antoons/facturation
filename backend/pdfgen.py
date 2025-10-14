from dateutil import parser

date = parser.parse("2024-12-01T00:00:00")
print(date.strftime("%d/%m/%Y"))