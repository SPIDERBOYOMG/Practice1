from datetime import date, timedelta

current_date = date.today()
new_date = current_date - timedelta(days=5)
print("Current Date:", current_date)
print("Date after subtracting 5 days:", new_date)

today = date.today()
yesterday = today - timedelta(days=1)
tomorrow = today + timedelta(days=1)

print("Yesterday:", yesterday)
print("Today:", today)
print("Tomorrow:", tomorrow)

now = datetime.now()
print("With microseconds:", now)
print("Without microseconds:", now.replace(microsecond=0))

# Example dates
date1 = datetime(2026, 2, 24, 12, 0, 0)
date2 = datetime(2026, 2, 25, 12, 0, 0)

difference = (date2 - date1).total_seconds()
print("Difference in seconds:", difference)
