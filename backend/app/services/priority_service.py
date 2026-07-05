"""
Priority Service — Classifies medicines by stock urgency level.
"""

from app.models.medicine import Priority


def classify_priority(current_stock: int, minimum_stock: int = 10) -> Priority:
    """
    Classify a medicine's priority based on current stock.
    
    Rules:
        Stock = 0          → CRITICAL (Red)
        Stock 1-5          → HIGH (Orange)
        Stock 6-9          → MEDIUM (Yellow)
        Stock >= minimum   → SAFE (Green)
    """
    if current_stock == 0:
        return Priority.CRITICAL
    elif current_stock <= 5:
        return Priority.HIGH
    elif current_stock < minimum_stock:
        return Priority.MEDIUM
    else:
        return Priority.SAFE


def get_priority_color(priority: Priority) -> str:
    """Get the display color for a priority level."""
    colors = {
        Priority.CRITICAL: "#EF4444",  # Red
        Priority.HIGH: "#F97316",      # Orange
        Priority.MEDIUM: "#EAB308",    # Yellow
        Priority.SAFE: "#22C55E",      # Green
    }
    return colors.get(priority, "#6B7280")


def get_priority_label(priority: Priority) -> str:
    """Get the display label for a priority level."""
    labels = {
        Priority.CRITICAL: "Critical",
        Priority.HIGH: "High",
        Priority.MEDIUM: "Medium",
        Priority.SAFE: "Safe",
    }
    return labels.get(priority, "Unknown")


def get_priority_order(priority: Priority) -> int:
    """Get sort order for priority (lower = more urgent)."""
    order = {
        Priority.CRITICAL: 0,
        Priority.HIGH: 1,
        Priority.MEDIUM: 2,
        Priority.SAFE: 3,
    }
    return order.get(priority, 4)
