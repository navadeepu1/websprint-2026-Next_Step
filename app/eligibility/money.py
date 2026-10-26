def format_inr(amount: int) -> str:
    value = str(int(amount))
    if len(value) <= 3:
        return f"₹{value}"
    last_three = value[-3:]
    remaining = value[:-3]
    groups: list[str] = []
    while remaining:
        groups.append(remaining[-2:])
        remaining = remaining[:-2]
    grouped = ",".join(reversed(groups))
    return f"₹{grouped},{last_three}"
