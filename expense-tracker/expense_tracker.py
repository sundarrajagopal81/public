#!/usr/bin/env python3
"""Simple monthly expense tracker — stores expenses in expenses.json."""

import json
import os
import sys
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(__file__), "expenses.json")

CATEGORIES = [
    "Food", "Transport", "Housing", "Utilities",
    "Entertainment", "Health", "Shopping", "Other"
]


# ---------- persistence ----------

def load() -> list[dict]:
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE) as f:
        return json.load(f)


def save(expenses: list[dict]) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(expenses, f, indent=2)


# ---------- helpers ----------

def next_id(expenses: list[dict]) -> int:
    return max((e["id"] for e in expenses), default=0) + 1


def fmt_amount(amount: float) -> str:
    return f"${amount:,.2f}"


def parse_month(month_str: str) -> tuple[int, int]:
    """Accept 'YYYY-MM' or 'MM' (assumes current year)."""
    if "-" in month_str:
        year, month = month_str.split("-")
        return int(year), int(month)
    today = datetime.today()
    return today.year, int(month_str)


# ---------- commands ----------

def cmd_add(args: list[str]) -> None:
    """add <amount> <category> [description] [YYYY-MM-DD]"""
    if len(args) < 2:
        print("Usage: add <amount> <category> [description] [date YYYY-MM-DD]")
        sys.exit(1)

    try:
        amount = float(args[0])
    except ValueError:
        print(f"Invalid amount: {args[0]}")
        sys.exit(1)

    category = args[1].capitalize()
    if category not in CATEGORIES:
        print(f"Unknown category '{category}'. Choose from: {', '.join(CATEGORIES)}")
        sys.exit(1)

    description = args[2] if len(args) > 2 else ""
    if len(args) > 3:
        date_str = args[3]
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print(f"Invalid date '{date_str}'. Use YYYY-MM-DD.")
            sys.exit(1)
    else:
        date_str = datetime.today().strftime("%Y-%m-%d")

    expenses = load()
    entry = {
        "id": next_id(expenses),
        "amount": round(amount, 2),
        "category": category,
        "description": description,
        "date": date_str,
    }
    expenses.append(entry)
    save(expenses)
    print(f"Added #{entry['id']}: {fmt_amount(amount)} [{category}] on {date_str}"
          + (f" — {description}" if description else ""))


def cmd_list(args: list[str]) -> None:
    """list [YYYY-MM]  — defaults to current month"""
    expenses = load()
    if not expenses:
        print("No expenses recorded yet.")
        return

    if args:
        year, month = parse_month(args[0])
    else:
        today = datetime.today()
        year, month = today.year, today.month

    filtered = [e for e in expenses
                if e["date"].startswith(f"{year}-{month:02d}")]

    label = f"{year}-{month:02d}"
    if not filtered:
        print(f"No expenses for {label}.")
        return

    print(f"\n{'ID':>4}  {'Date':<12}  {'Category':<14}  {'Amount':>10}  Description")
    print("-" * 65)
    for e in sorted(filtered, key=lambda x: x["date"]):
        print(f"{e['id']:>4}  {e['date']:<12}  {e['category']:<14}  "
              f"{fmt_amount(e['amount']):>10}  {e['description']}")
    total = sum(e["amount"] for e in filtered)
    print("-" * 65)
    print(f"{'Total':>43}  {fmt_amount(total):>10}")
    print()


def cmd_summary(args: list[str]) -> None:
    """summary [YYYY-MM]  — totals by category for a month"""
    expenses = load()
    if not expenses:
        print("No expenses recorded yet.")
        return

    if args:
        year, month = parse_month(args[0])
    else:
        today = datetime.today()
        year, month = today.year, today.month

    filtered = [e for e in expenses
                if e["date"].startswith(f"{year}-{month:02d}")]

    label = f"{year}-{month:02d}"
    if not filtered:
        print(f"No expenses for {label}.")
        return

    totals: dict[str, float] = {}
    for e in filtered:
        totals[e["category"]] = totals.get(e["category"], 0) + e["amount"]

    grand = sum(totals.values())
    print(f"\nSummary for {label}")
    print("-" * 35)
    for cat, amt in sorted(totals.items(), key=lambda x: -x[1]):
        bar = "#" * int(amt / grand * 20)
        print(f"  {cat:<14} {fmt_amount(amt):>10}  {bar}")
    print("-" * 35)
    print(f"  {'Total':<14} {fmt_amount(grand):>10}")
    print()


def cmd_delete(args: list[str]) -> None:
    """delete <id>"""
    if not args:
        print("Usage: delete <id>")
        sys.exit(1)
    try:
        eid = int(args[0])
    except ValueError:
        print(f"Invalid id: {args[0]}")
        sys.exit(1)

    expenses = load()
    before = len(expenses)
    expenses = [e for e in expenses if e["id"] != eid]
    if len(expenses) == before:
        print(f"No expense with id {eid}.")
        sys.exit(1)
    save(expenses)
    print(f"Deleted expense #{eid}.")


def cmd_report(args: list[str]) -> None:
    """report [YYYY-MM]  — generate an HTML report file"""
    expenses = load()

    if args:
        year, month = parse_month(args[0])
    else:
        today = datetime.today()
        year, month = today.year, today.month

    filtered = sorted(
        [e for e in expenses if e["date"].startswith(f"{year}-{month:02d}")],
        key=lambda x: x["date"]
    )

    label = f"{year}-{month:02d}"
    totals: dict[str, float] = {}
    for e in filtered:
        totals[e["category"]] = totals.get(e["category"], 0) + e["amount"]
    grand = sum(totals.values())

    rows = "\n".join(
        "<tr><td>{}</td><td>{}</td><td>{}</td><td class='amt'>${:.2f}</td><td>{}</td></tr>".format(
            e["id"], e["date"], e["category"], e["amount"], e["description"]
        )
        for e in filtered
    )

    cat_labels = list(totals.keys())
    cat_values = [totals[c] for c in cat_labels]

    category_rows = "\n".join(
        "<tr><td>{}</td><td class='amt'>${:.2f}</td><td>{:.1f}%</td></tr>".format(
            cat, amt, amt / grand * 100
        )
        for cat, amt in sorted(totals.items(), key=lambda x: -x[1])
    )

    avg = grand / len(filtered) if filtered else 0

    if filtered:
        body_content = (
            '<div style="display:flex;gap:2rem;flex-wrap:wrap;align-items:flex-start">\n'
            '<div class="chart-wrap">\n'
            '  <h2>By Category</h2>\n'
            '  <canvas id="pie" width="360" height="360"></canvas>\n'
            '</div>\n'
            '<div style="flex:1;min-width:280px">\n'
            '  <h2>Category Breakdown</h2>\n'
            '  <table>\n'
            '    <thead><tr><th>Category</th><th class="amt">Amount</th><th>Share</th></tr></thead>\n'
            '    <tbody>' + category_rows + '</tbody>\n'
            '    <tfoot><tr><td>Total</td><td class="amt">${:.2f}</td><td>100%</td></tr></tfoot>\n'.format(grand) +
            '  </table>\n'
            '</div>\n'
            '</div>\n'
            '<h2 style="margin-top:2rem">All Transactions</h2>\n'
            '<table>\n'
            '  <thead><tr><th>#</th><th>Date</th><th>Category</th><th class="amt">Amount</th><th>Description</th></tr></thead>\n'
            '  <tbody>' + rows + '</tbody>\n'
            '  <tfoot><tr><td colspan="3">Total</td><td class="amt">${:.2f}</td><td></td></tr></tfoot>\n'.format(grand) +
            '</table>\n'
        )
    else:
        body_content = '<p class="empty">No expenses recorded for this period.</p>\n'

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Expense Report &mdash; {label}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: system-ui, sans-serif; background: #f5f7fa; color: #333; padding: 2rem; }}
  h1 {{ font-size: 1.6rem; margin-bottom: 0.25rem; }}
  .sub {{ color: #666; margin-bottom: 2rem; font-size: 0.9rem; }}
  .cards {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 2rem; }}
  .card {{ background: #fff; border-radius: 10px; padding: 1.2rem 1.6rem;
            box-shadow: 0 1px 4px rgba(0,0,0,.08); min-width: 160px; }}
  .card .label {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: .05em; color: #888; }}
  .card .value {{ font-size: 1.8rem; font-weight: 700; color: #2563eb; margin-top: .2rem; }}
  h2 {{ font-size: 1.1rem; margin-bottom: .75rem; margin-top: 2rem; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff;
           border-radius: 10px; overflow: hidden;
           box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
  th, td {{ padding: .65rem 1rem; text-align: left; font-size: .9rem; }}
  th {{ background: #2563eb; color: #fff; font-weight: 600; }}
  tr:nth-child(even) {{ background: #f0f4ff; }}
  .amt {{ text-align: right; font-variant-numeric: tabular-nums; }}
  tfoot td {{ font-weight: 700; background: #e8f0fe; }}
  .chart-wrap {{ background: #fff; border-radius: 10px; padding: 1.5rem;
                 box-shadow: 0 1px 4px rgba(0,0,0,.08); max-width: 420px; }}
  canvas {{ max-width: 100%; }}
  .empty {{ color: #888; font-style: italic; }}
</style>
</head>
<body>
<h1>Monthly Expense Report</h1>
<p class="sub">Period: <strong>{label}</strong> &nbsp;|&nbsp; Generated: {generated}</p>

<div class="cards">
  <div class="card"><div class="label">Total Spent</div><div class="value">${grand}</div></div>
  <div class="card"><div class="label">Transactions</div><div class="value">{txn_count}</div></div>
  <div class="card"><div class="label">Categories</div><div class="value">{cat_count}</div></div>
  <div class="card"><div class="label">Avg per Transaction</div><div class="value">${avg}</div></div>
</div>

{body_content}
<script>
(function() {{
  var labels = {cat_labels_json};
  var values = {cat_values_json};
  if (!labels.length) return;
  var canvas = document.getElementById('pie');
  if (!canvas) return;
  var ctx = canvas.getContext('2d');
  var colors = ['#2563eb','#10b981','#f59e0b','#ef4444','#8b5cf6','#ec4899','#06b6d4','#84cc16'];
  var total = values.reduce(function(a,b){{return a+b;}}, 0);
  var start = -Math.PI / 2;
  var cx = canvas.width/2, cy = canvas.height/2, r = Math.min(cx,cy) - 40;
  values.forEach(function(v, i) {{
    var slice = (v / total) * 2 * Math.PI;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, start, start + slice);
    ctx.closePath();
    ctx.fillStyle = colors[i % colors.length];
    ctx.fill();
    var mid = start + slice / 2;
    var lx = cx + (r * 0.65) * Math.cos(mid);
    var ly = cy + (r * 0.65) * Math.sin(mid);
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 12px system-ui';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    if (v / total > 0.05) ctx.fillText(labels[i], lx, ly);
    start += slice;
  }});
  var legendY = cy + r + 16;
  labels.forEach(function(l, i) {{
    var lx = 16 + (i % 4) * 88;
    var ly = legendY + Math.floor(i / 4) * 20;
    ctx.fillStyle = colors[i % colors.length];
    ctx.fillRect(lx, ly, 12, 12);
    ctx.fillStyle = '#333';
    ctx.font = '11px system-ui';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText(l, lx + 16, ly);
  }});
}})();
</script>
</body>
</html>""".format(
        label=label,
        generated=datetime.today().strftime("%Y-%m-%d %H:%M"),
        grand="{:,.2f}".format(grand),
        txn_count=len(filtered),
        cat_count=len(totals),
        avg="{:,.2f}".format(avg),
        body_content=body_content,
        cat_labels_json=json.dumps(cat_labels),
        cat_values_json=json.dumps(cat_values),
    )

    out_file = os.path.join(os.path.dirname(__file__), f"report_{label}.html")
    with open(out_file, "w") as f:
        f.write(html)
    print(f"Report saved to: {out_file}")


def cmd_help() -> None:
    print("""
Expense Tracker — commands
  add <amount> <category> [description] [YYYY-MM-DD]
      Record a new expense (date defaults to today)
      Categories: Food, Transport, Housing, Utilities,
                  Entertainment, Health, Shopping, Other

  list [YYYY-MM]
      List all expenses for a month (default: current month)

  summary [YYYY-MM]
      Show totals by category (default: current month)

  delete <id>
      Remove an expense by its ID

  report [YYYY-MM]
      Generate an HTML report file (default: current month)

  help
      Show this message
""")


# ---------- entry point ----------

COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "summary": cmd_summary,
    "delete": cmd_delete,
    "report": cmd_report,
    "help": lambda _: cmd_help(),
}


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ("help", "--help", "-h"):
        cmd_help()
        return
    cmd = args[0].lower()
    if cmd not in COMMANDS:
        print(f"Unknown command '{cmd}'. Run 'help' to see available commands.")
        sys.exit(1)
    COMMANDS[cmd](args[1:])


if __name__ == "__main__":
    main()
