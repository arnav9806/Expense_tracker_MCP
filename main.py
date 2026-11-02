from fastmcp import FastMCP
import os
import sqlite3
import csv
import io
import json
from datetime import datetime

import logging
import traceback

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger("expense-tracker")

# ============================================================
# LOCAL CONFIGURATION
# ============================================================

# DB_PATH = os.path.join(
#     os.path.dirname(__file__),
#     "expenses.db"
# )

# CATEGORIES_PATH = os.path.join(
#     os.path.dirname(__file__),
#     "categories.json"
# )

# mcp = FastMCP("demo-expense-tracker")


# ============================================================
# DATABASE HELPERS for LOCAl
# ============================================================

# def get_connection():
#     """Create and return a SQLite database connection."""

#     conn = sqlite3.connect(DB_PATH)
#     conn.row_factory = sqlite3.Row

#     return conn


# def init_db():
#     """Create required database tables."""

#     with get_connection() as c:

#         # Expenses table
#         c.execute("""
#             CREATE TABLE IF NOT EXISTS expenses(
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 date TEXT NOT NULL,
#                 amount REAL NOT NULL,
#                 category TEXT NOT NULL,
#                 subcategory TEXT DEFAULT '',
#                 note TEXT DEFAULT ''
#             )
#         """)

#         # Budgets table
#         c.execute("""
#             CREATE TABLE IF NOT EXISTS budgets(
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 month TEXT NOT NULL,
#                 category TEXT NOT NULL,
#                 amount REAL NOT NULL,
#                 UNIQUE(month, category)
#             )
#         """)


# init_db()
# ============================================================
# DATABASE HELPERS for PRODUCTION
# ============================================================
# ============================================================
# PRODUCTION CONFIGURATION
# ============================================================


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = "/tmp/expenses.db"
CATEGORIES_PATH = os.path.join(BASE_DIR, "categories.json")

mcp = FastMCP("expense-tracker")


def get_connection():
    os.makedirs("/tmp", exist_ok=True)

    conn = sqlite3.connect("/tmp/expenses.db", timeout=30)
    conn.row_factory = sqlite3.Row

    logger.info("SQLite connected successfully: /tmp/expenses.db")
    return conn

def init_db():
    """Create required database tables."""

    try:
        logger.info("Initializing SQLite database: %s", DB_PATH)

        with get_connection() as c:

            logger.info("Creating expenses table...")

            c.execute("""
                CREATE TABLE IF NOT EXISTS expenses(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT DEFAULT '',
                    note TEXT DEFAULT ''
                )
            """)

            logger.info("Expenses table created successfully")

            logger.info("Creating budgets table...")

            c.execute("""
                CREATE TABLE IF NOT EXISTS budgets(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    month TEXT NOT NULL,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    UNIQUE(month, category)
                )
            """)

            logger.info("Budgets table created successfully")

        logger.info("Database initialization completed successfully")

    except Exception:
        logger.exception("Database initialization failed")
        raise


init_db()


# ============================================================
# VALIDATION HELPERS
# ============================================================

def validate_date(date_string):
    """Validate YYYY-MM-DD format."""

    try:
        datetime.strptime(date_string, "%Y-%m-%d")
        return True

    except (ValueError, TypeError):
        return False


def validate_month(month):
    """Validate YYYY-MM format."""

    try:
        datetime.strptime(month, "%Y-%m")
        return True

    except (ValueError, TypeError):
        return False


def validate_amount(amount):
    """Validate that amount is a positive number."""

    try:
        amount = float(amount)

        return amount > 0

    except (TypeError, ValueError):
        return False


def row_to_dict(row):
    """Convert SQLite Row into dictionary."""

    return dict(row)


# ============================================================
# 1. ADD EXPENSE
# ============================================================

@mcp.tool()
def add_expense(
    date,
    amount,
    category,
    subcategory="",
    note=""
):
    """
    Add a new expense.

    date: YYYY-MM-DD
    amount: Positive expense amount
    category: Expense category
    subcategory: Optional subcategory
    note: Optional note
    """

    if not validate_date(date):
        return {
            "status": "error",
            "message": "Invalid date. Use YYYY-MM-DD format."
        }

    if not validate_amount(amount):
        return {
            "status": "error",
            "message": "Amount must be greater than 0."
        }

    with get_connection() as c:

        cur = c.execute(
            """
            INSERT INTO expenses
            (
                date,
                amount,
                category,
                subcategory,
                note
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                date,
                float(amount),
                category,
                subcategory,
                note
            )
        )

        return {
            "status": "ok",
            "message": "Expense added successfully.",
            "id": cur.lastrowid
        }


# ============================================================
# 2. GET EXPENSE
# ============================================================

@mcp.tool()
def get_expense(expense_id):
    """
    Get a single expense by internal ID.

    Normally users do not need to provide the ID.
    This tool is useful for internal lookup/debugging.
    """

    with get_connection() as c:

        row = c.execute(
            """
            SELECT
                id,
                date,
                amount,
                category,
                subcategory,
                note
            FROM expenses
            WHERE id = ?
            """,
            (expense_id,)
        ).fetchone()

        if not row:

            return {
                "status": "error",
                "message": (
                    f"Expense with ID {expense_id} "
                    "was not found."
                )
            }

        return row_to_dict(row)


# ============================================================
# 3. LIST EXPENSES
# ============================================================

@mcp.tool()
def list_expenses(
    start_date,
    end_date
):
    """
    List expenses within an inclusive date range.

    Dates must use YYYY-MM-DD format.
    """

    if not validate_date(start_date):
        return {
            "status": "error",
            "message": "Invalid start_date."
        }

    if not validate_date(end_date):
        return {
            "status": "error",
            "message": "Invalid end_date."
        }

    with get_connection() as c:

        rows = c.execute(
            """
            SELECT
                id,
                date,
                amount,
                category,
                subcategory,
                note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY date ASC, id ASC
            """,
            (
                start_date,
                end_date
            )
        ).fetchall()

        return [
            row_to_dict(row)
            for row in rows
        ]


# ============================================================
# 4. FIND EXPENSE
# ============================================================

def find_matching_expenses(
    date,
    amount,
    category,
    subcategory=None
):
    """
    Find expenses using user-friendly identifying information.

    Required:
        date
        amount
        category

    Optional:
        subcategory

    This function is intentionally internal and is used by
    update_expense and delete_expense.
    """

    query = """
        SELECT
            id,
            date,
            amount,
            category,
            subcategory,
            note
        FROM expenses
        WHERE date = ?
        AND amount = ?
        AND LOWER(category) = LOWER(?)
    """

    params = [
        date,
        float(amount),
        category
    ]

    if subcategory:
        query += """
            AND LOWER(subcategory) = LOWER(?)
        """

        params.append(subcategory)

    query += """
        ORDER BY id ASC
    """

    with get_connection() as c:

        rows = c.execute(
            query,
            params
        ).fetchall()

        return [
            row_to_dict(row)
            for row in rows
        ]


# ============================================================
# 5. UPDATE EXPENSE
# ============================================================

@mcp.tool()
def update_expense(
    date,
    amount,
    category,
    new_date=None,
    new_amount=None,
    new_category=None,
    new_subcategory=None,
    new_note=None,
    subcategory=None
):
    """
    Update an expense without requiring the user to know its ID.

    Existing expense is identified using:

        date
        amount
        category

    Optional subcategory can make the match more specific.

    Example:

        Update my ₹500 Food expense from 2026-08-15
        to ₹700.

    If multiple expenses match, no update is performed.
    """

    # Validate identifying information

    if not validate_date(date):

        return {
            "status": "error",
            "message": (
                "Invalid date. "
                "Use YYYY-MM-DD format."
            )
        }

    if not validate_amount(amount):

        return {
            "status": "error",
            "message": (
                "Amount must be greater than 0."
            )
        }

    if not category:

        return {
            "status": "error",
            "message": "Category is required."
        }

    # Validate new values if provided

    if new_date is not None:

        if not validate_date(new_date):

            return {
                "status": "error",
                "message": (
                    "Invalid new_date. "
                    "Use YYYY-MM-DD format."
                )
            }

    if new_amount is not None:

        if not validate_amount(new_amount):

            return {
                "status": "error",
                "message": (
                    "new_amount must be greater than 0."
                )
            }

    # Find matching expenses

    matches = find_matching_expenses(
        date=date,
        amount=amount,
        category=category,
        subcategory=subcategory
    )

    # No matching record

    if len(matches) == 0:

        return {
            "status": "not_found",
            "message": (
                "No expense matched the provided "
                "date, amount, category and "
                "subcategory."
            )
        }

    # Multiple matching records

    if len(matches) > 1:

        return {
            "status": "multiple_matches",
            "message": (
                "Multiple expenses matched. "
                "Please provide more information "
                "such as the subcategory or note."
            ),
            "matches": matches
        }

    # Exactly one matching record

    expense = matches[0]

    updated_date = (
        new_date
        if new_date is not None
        else expense["date"]
    )

    updated_amount = (
        float(new_amount)
        if new_amount is not None
        else expense["amount"]
    )

    updated_category = (
        new_category
        if new_category is not None
        else expense["category"]
    )

    updated_subcategory = (
        new_subcategory
        if new_subcategory is not None
        else expense["subcategory"]
    )

    updated_note = (
        new_note
        if new_note is not None
        else expense["note"]
    )

    with get_connection() as c:

        c.execute(
            """
            UPDATE expenses
            SET
                date = ?,
                amount = ?,
                category = ?,
                subcategory = ?,
                note = ?
            WHERE id = ?
            """,
            (
                updated_date,
                updated_amount,
                updated_category,
                updated_subcategory,
                updated_note,
                expense["id"]
            )
        )

        return {
            "status": "ok",
            "message": "Expense updated successfully.",
            "expense": {
                "id": expense["id"],
                "date": updated_date,
                "amount": updated_amount,
                "category": updated_category,
                "subcategory": updated_subcategory,
                "note": updated_note
            }
        }


# ============================================================
# 6. DELETE EXPENSE
# ============================================================

@mcp.tool()
def delete_expense(
    date,
    amount,
    category,
    subcategory=None
):
    """
    Delete an expense without requiring the user to know its ID.

    The expense is identified using:

        date
        amount
        category

    Optional subcategory can make the match more specific.

    If multiple records match, nothing is deleted.
    """

    # Validate input

    if not validate_date(date):

        return {
            "status": "error",
            "message": (
                "Invalid date. "
                "Use YYYY-MM-DD format."
            )
        }

    if not validate_amount(amount):

        return {
            "status": "error",
            "message": (
                "Amount must be greater than 0."
            )
        }

    if not category:

        return {
            "status": "error",
            "message": "Category is required."
        }

    # Find matches

    matches = find_matching_expenses(
        date=date,
        amount=amount,
        category=category,
        subcategory=subcategory
    )

    # No match

    if len(matches) == 0:

        return {
            "status": "not_found",
            "message": (
                "No expense matched the provided "
                "date, amount, category and "
                "subcategory."
            )
        }

    # Multiple matches

    if len(matches) > 1:

        return {
            "status": "multiple_matches",
            "message": (
                "Multiple expenses matched. "
                "Nothing was deleted. "
                "Please provide more information."
            ),
            "matches": matches
        }

    # Exactly one match

    expense = matches[0]

    with get_connection() as c:

        c.execute(
            """
            DELETE FROM expenses
            WHERE id = ?
            """,
            (expense["id"],)
        )

        return {
            "status": "ok",
            "message": "Expense deleted successfully.",
            "deleted_expense": expense
        }


# ============================================================
# 7. SEARCH EXPENSES
# ============================================================

@mcp.tool()
def search_expenses(search_text):
    """
    Search expenses by category, subcategory or note.
    """

    if not search_text:

        return {
            "status": "error",
            "message": "Search text is required."
        }

    search_pattern = f"%{search_text}%"

    with get_connection() as c:

        rows = c.execute(
            """
            SELECT
                id,
                date,
                amount,
                category,
                subcategory,
                note
            FROM expenses
            WHERE category LIKE ?
               OR subcategory LIKE ?
               OR note LIKE ?
            ORDER BY date DESC, id DESC
            """,
            (
                search_pattern,
                search_pattern,
                search_pattern
            )
        ).fetchall()

        return [
            row_to_dict(row)
            for row in rows
        ]


# ============================================================
# 8. FILTER EXPENSES
# ============================================================

@mcp.tool()
def filter_expenses(
    start_date=None,
    end_date=None,
    category=None,
    min_amount=None,
    max_amount=None
):
    """
    Filter expenses using optional:

        start_date
        end_date
        category
        min_amount
        max_amount
    """

    query = """
        SELECT
            id,
            date,
            amount,
            category,
            subcategory,
            note
        FROM expenses
        WHERE 1 = 1
    """

    params = []

    if start_date:

        if not validate_date(start_date):

            return {
                "status": "error",
                "message": "Invalid start_date."
            }

        query += " AND date >= ?"
        params.append(start_date)

    if end_date:

        if not validate_date(end_date):

            return {
                "status": "error",
                "message": "Invalid end_date."
            }

        query += " AND date <= ?"
        params.append(end_date)

    if category:

        query += """
            AND LOWER(category) = LOWER(?)
        """

        params.append(category)

    if min_amount is not None:

        if not validate_amount(min_amount):

            return {
                "status": "error",
                "message": "Invalid min_amount."
            }

        query += " AND amount >= ?"
        params.append(float(min_amount))

    if max_amount is not None:

        if not validate_amount(max_amount):

            return {
                "status": "error",
                "message": "Invalid max_amount."
            }

        query += " AND amount <= ?"
        params.append(float(max_amount))

    query += """
        ORDER BY date DESC, id DESC
    """

    with get_connection() as c:

        rows = c.execute(
            query,
            params
        ).fetchall()

        return [
            row_to_dict(row)
            for row in rows
        ]


# ============================================================
# 9. SUMMARIZE EXPENSES
# ============================================================

@mcp.tool()
def summarize(
    start_date,
    end_date,
    category=None
):
    """
    Summarize expenses by category.

    Returns:
        transaction count
        total amount
        average amount
    """

    if not validate_date(start_date):

        return {
            "status": "error",
            "message": "Invalid start_date."
        }

    if not validate_date(end_date):

        return {
            "status": "error",
            "message": "Invalid end_date."
        }

    query = """
        SELECT
            category,
            COUNT(*) AS transaction_count,
            SUM(amount) AS total_amount,
            AVG(amount) AS average_amount
        FROM expenses
        WHERE date BETWEEN ? AND ?
    """

    params = [
        start_date,
        end_date
    ]

    if category:

        query += """
            AND LOWER(category) = LOWER(?)
        """

        params.append(category)

    query += """
        GROUP BY category
        ORDER BY total_amount DESC
    """

    with get_connection() as c:

        rows = c.execute(
            query,
            params
        ).fetchall()

        return [
            row_to_dict(row)
            for row in rows
        ]


# ============================================================
# 10. CATEGORY SUMMARY
# ============================================================

@mcp.tool()
def category_summary(
    start_date,
    end_date
):
    """
    Return spending breakdown by category.

    Also calculates each category's percentage
    of total spending.
    """

    if not validate_date(start_date):

        return {
            "status": "error",
            "message": "Invalid start_date."
        }

    if not validate_date(end_date):

        return {
            "status": "error",
            "message": "Invalid end_date."
        }

    with get_connection() as c:

        rows = c.execute(
            """
            SELECT
                category,
                COUNT(*) AS transaction_count,
                SUM(amount) AS total_amount
            FROM expenses
            WHERE date BETWEEN ? AND ?
            GROUP BY category
            ORDER BY total_amount DESC
            """,
            (
                start_date,
                end_date
            )
        ).fetchall()

    total = sum(
        row["total_amount"]
        for row in rows
    )

    result = []

    for row in rows:

        percentage = (
            (row["total_amount"] / total) * 100
            if total > 0
            else 0
        )

        result.append({
            "category": row["category"],
            "transaction_count": row["transaction_count"],
            "total_amount": round(
                row["total_amount"],
                2
            ),
            "percentage": round(
                percentage,
                2
            )
        })

    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "total_spending": round(
            total,
            2
        ),
        "categories": result
    }


# ============================================================
# 11. MONTHLY SUMMARY
# ============================================================

@mcp.tool()
def monthly_summary(year):
    """
    Return monthly spending summary for a year.
    """

    try:
        year = int(year)

        if year < 2000 or year > 2100:
            raise ValueError

    except (TypeError, ValueError):

        return {
            "status": "error",
            "message": "Invalid year."
        }

    with get_connection() as c:

        rows = c.execute(
            """
            SELECT
                substr(date, 1, 7) AS month,
                COUNT(*) AS transaction_count,
                SUM(amount) AS total_amount,
                AVG(amount) AS average_amount
            FROM expenses
            WHERE substr(date, 1, 4) = ?
            GROUP BY substr(date, 1, 7)
            ORDER BY month ASC
            """,
            (str(year),)
        ).fetchall()

        return [
            row_to_dict(row)
            for row in rows
        ]


# ============================================================
# 12. TOP EXPENSES
# ============================================================

@mcp.tool()
def top_expenses(
    start_date,
    end_date,
    limit=5
):
    """
    Return the highest-value expenses in a date range.
    """

    if not validate_date(start_date):

        return {
            "status": "error",
            "message": "Invalid start_date."
        }

    if not validate_date(end_date):

        return {
            "status": "error",
            "message": "Invalid end_date."
        }

    try:

        limit = int(limit)

        if limit <= 0:
            raise ValueError

    except (TypeError, ValueError):

        return {
            "status": "error",
            "message": (
                "Limit must be a positive integer."
            )
        }

    with get_connection() as c:

        rows = c.execute(
            """
            SELECT
                id,
                date,
                amount,
                category,
                subcategory,
                note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY amount DESC
            LIMIT ?
            """,
            (
                start_date,
                end_date,
                limit
            )
        ).fetchall()

        return [
            row_to_dict(row)
            for row in rows
        ]


# ============================================================
# 13. SPENDING TRENDS
# ============================================================

@mcp.tool()
def spending_trends(
    start_date,
    end_date
):
    """
    Analyze monthly spending trends.
    """

    if not validate_date(start_date):

        return {
            "status": "error",
            "message": "Invalid start_date."
        }

    if not validate_date(end_date):

        return {
            "status": "error",
            "message": "Invalid end_date."
        }

    with get_connection() as c:

        rows = c.execute(
            """
            SELECT
                substr(date, 1, 7) AS month,
                SUM(amount) AS total_amount,
                COUNT(*) AS transaction_count
            FROM expenses
            WHERE date BETWEEN ? AND ?
            GROUP BY substr(date, 1, 7)
            ORDER BY month ASC
            """,
            (
                start_date,
                end_date
            )
        ).fetchall()

    data = [
        row_to_dict(row)
        for row in rows
    ]

    for row in data:

        row["total_amount"] = round(
            row["total_amount"],
            2
        )

    if len(data) >= 2:

        previous = data[-2]["total_amount"]
        current = data[-1]["total_amount"]

        if previous > 0:

            change_percentage = (
                (current - previous)
                / previous
            ) * 100

        else:

            change_percentage = 0

        if current > previous:

            trend = "increasing"

        elif current < previous:

            trend = "decreasing"

        else:

            trend = "stable"

    else:

        change_percentage = 0
        trend = "insufficient_data"

    return {
        "monthly_data": data,
        "latest_trend": trend,
        "change_percentage": round(
            change_percentage,
            2
        )
    }


# ============================================================
# 14. SET BUDGET
# ============================================================

@mcp.tool()
def set_budget(
    month,
    category,
    amount
):
    """
    Set or update a monthly budget.

    month: YYYY-MM
    category: Specific category or 'overall'
    amount: Positive budget amount
    """

    if not validate_month(month):

        return {
            "status": "error",
            "message": (
                "Month must use YYYY-MM format."
            )
        }

    if not validate_amount(amount):

        return {
            "status": "error",
            "message": (
                "Budget amount must be greater than 0."
            )
        }

    with get_connection() as c:

        c.execute(
            """
            INSERT INTO budgets
            (
                month,
                category,
                amount
            )
            VALUES (?, ?, ?)

            ON CONFLICT(month, category)
            DO UPDATE SET
                amount = excluded.amount
            """,
            (
                month,
                category,
                float(amount)
            )
        )

    return {
        "status": "ok",
        "message": "Budget saved successfully.",
        "month": month,
        "category": category,
        "amount": float(amount)
    }


# ============================================================
# 15. GET BUDGET
# ============================================================

@mcp.tool()
def get_budget(
    month,
    category=None
):
    """
    Get budget information for a month.
    """

    if not validate_month(month):

        return {
            "status": "error",
            "message": (
                "Month must use YYYY-MM format."
            )
        }

    query = """
        SELECT
            id,
            month,
            category,
            amount
        FROM budgets
        WHERE month = ?
    """

    params = [month]

    if category:

        query += """
            AND LOWER(category) = LOWER(?)
        """

        params.append(category)

    query += """
        ORDER BY category ASC
    """

    with get_connection() as c:

        rows = c.execute(
            query,
            params
        ).fetchall()

        return [
            row_to_dict(row)
            for row in rows
        ]


# ============================================================
# 16. BUDGET STATUS
# ============================================================

@mcp.tool()
def budget_status(
    month,
    category="overall"
):
    """
    Compare actual spending against budget.

    category can be:
        overall
        Food
        Travel
        Shopping
        etc.
    """

    if not validate_month(month):

        return {
            "status": "error",
            "message": (
                "Month must use YYYY-MM format."
            )
        }

    with get_connection() as c:

        budget = c.execute(
            """
            SELECT amount
            FROM budgets
            WHERE month = ?
            AND LOWER(category) = LOWER(?)
            """,
            (
                month,
                category
            )
        ).fetchone()

        if not budget:

            return {
                "status": "error",
                "message": (
                    f"No budget found for "
                    f"{month} / {category}."
                )
            }

        if category.lower() == "overall":

            spending = c.execute(
                """
                SELECT
                    COALESCE(SUM(amount), 0)
                FROM expenses
                WHERE date >= ?
                AND date < date(?, '+1 month')
                """,
                (
                    f"{month}-01",
                    f"{month}-01"
                )
            ).fetchone()[0]

        else:

            spending = c.execute(
                """
                SELECT
                    COALESCE(SUM(amount), 0)
                FROM expenses
                WHERE date >= ?
                AND date < date(?, '+1 month')
                AND LOWER(category) = LOWER(?)
                """,
                (
                    f"{month}-01",
                    f"{month}-01",
                    category
                )
            ).fetchone()[0]

    budget_amount = budget["amount"]

    remaining = (
        budget_amount - spending
    )

    percentage_used = (
        (spending / budget_amount) * 100
        if budget_amount > 0
        else 0
    )

    if percentage_used >= 100:

        status = "over_budget"

    elif percentage_used >= 80:

        status = "near_budget_limit"

    else:

        status = "within_budget"

    return {
        "month": month,
        "category": category,
        "budget": round(
            budget_amount,
            2
        ),
        "spent": round(
            spending,
            2
        ),
        "remaining": round(
            remaining,
            2
        ),
        "percentage_used": round(
            percentage_used,
            2
        ),
        "status": status
    }


# ============================================================
# 17. EXPORT EXPENSES
# ============================================================

@mcp.tool()
def export_expenses(
    start_date,
    end_date,
    format="csv"
):
    """
    Export expenses as CSV or JSON.

    Supported formats:
        csv
        json
    """

    if not validate_date(start_date):

        return {
            "status": "error",
            "message": "Invalid start_date."
        }

    if not validate_date(end_date):

        return {
            "status": "error",
            "message": "Invalid end_date."
        }

    format = format.lower()

    if format not in ("csv", "json"):

        return {
            "status": "error",
            "message": (
                "Supported formats are csv and json."
            )
        }

    with get_connection() as c:

        rows = c.execute(
            """
            SELECT
                id,
                date,
                amount,
                category,
                subcategory,
                note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY date ASC, id ASC
            """,
            (
                start_date,
                end_date
            )
        ).fetchall()

        data = [
            row_to_dict(row)
            for row in rows
        ]

    # JSON export

    if format == "json":

        return {
            "format": "json",
            "data": json.dumps(
                data,
                indent=2
            )
        }

    # CSV export

    output = io.StringIO()

    if data:

        writer = csv.DictWriter(
            output,
            fieldnames=data[0].keys()
        )

        writer.writeheader()
        writer.writerows(data)

    return {
        "format": "csv",
        "data": output.getvalue()
    }


# ============================================================
# RESOURCE: CATEGORIES
# ============================================================

@mcp.resource("expense:///categories", mime_type="application/json")  # Changed: expense:// → expense:///
def categories():
    try:
        # Provide default categories if file doesn't exist
        default_categories = {
            "categories": [
                "Food & Dining",
                "Transportation",
                "Shopping",
                "Entertainment",
                "Bills & Utilities",
                "Healthcare",
                "Travel",
                "Education",
                "Business",
                "Other"
            ]
        }
        
        try:
            with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            import json
            return json.dumps(default_categories, indent=2)
    except Exception as e:
        return f'{{"error": "Could not load categories: {str(e)}"}}'


# ============================================================
# RUN MCP SERVER ON LOCAL
# ============================================================
# if __name__ == "__main__":
#     mcp.run()

# ============================================================
# RUN MCP SERVER ON PRODUCTION
# ============================================================

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)