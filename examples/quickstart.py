"""quickstart.py — emotion library usage demo.

Run from the repo root:
    python examples/quickstart.py
"""
import sys
sys.path.insert(0, ".")

from checkemotion import emotion, show_dashboard


@emotion
def calculate_total(numbers: list) -> float:
    """Sum positive numbers in a list."""
    return sum(n for n in numbers if n > 0)


@emotion
def validate_user(user_id: int, role: str) -> bool:
    """Check that user_id is positive and role is non-empty."""
    try:
        assert user_id > 0, "user_id must be positive"
        assert role.strip(), "role must not be empty"
        return True
    except AssertionError:
        return False


@emotion
def get_config(key: str) -> str:
    """Retrieve a config value by key."""
    defaults = {"host": "localhost", "port": "8080", "debug": "false"}
    return defaults.get(key, "")


@emotion
def delete_expired_sessions(sessions: list) -> list:
    """Remove all expired sessions from the list."""
    return [s for s in sessions if not s.get("expired", False)]


@emotion
def generate_report(data: dict) -> dict:
    """Build and return a structured report dict from raw data."""
    report = {}
    for key, value in data.items():
        if isinstance(value, (int, float)):
            report[key] = {"value": value, "type": "numeric"}
        else:
            report[key] = {"value": str(value), "type": "text"}
    return report


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Running example calls...")
    print("=" * 60 + "\n")

    calculate_total([1, -2, 3, 4, -5])
    calculate_total([10, 20, 30])

    validate_user(42, "admin")
    validate_user(0, "")          # triggers exception path

    get_config("host")
    get_config("port")

    delete_expired_sessions([
        {"id": 1, "expired": False},
        {"id": 2, "expired": True},
    ])

    generate_report({"users": 150, "revenue": 9800.50, "plan": "pro"})

    print()
    show_dashboard()
