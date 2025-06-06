from datetime import datetime

def is_within_days_back(date_str, days_back, today=None):
    """
    Checks if the given date is within the specified number of days back from today.

    Args:
        date_str (str): Date string in format 'Jun 6, 2025'
        days_back (int): Number of days back to check
        today (datetime.date, optional): Reference date, defaults to today if None

    Returns:
        bool: True if the date is within days_back (0 is today), False otherwise
    """
    if today is None:
        today = datetime.today().date()

    target_date = datetime.strptime(date_str, "%b %d, %Y").date()
    delta_days = (today - target_date).days
    return 0 <= delta_days <= days_back

# Example usage
# print(is_within_days_back("Jun 6, 2025", 0))  # True if today is June 6, 2025
# print(is_within_days_back("Jun 5, 2025", 1))  # True if today is June 6, 2025
# print(is_within_days_back("Jun 5, 2025", 0))  # False if today is June 6, 2025