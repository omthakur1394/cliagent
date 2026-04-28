from rich.console import Console
from rich.panel import Panel
from rich import box

console = Console()

SEVERITY_COLORS = {
    "HIGH": "red",
    "MEDIUM": "yellow",
    "LOW": "green"
}

def parse_severity(review: str) -> str:
    for line in review.splitlines():
        # strip markdown bold ** so it parses correctly
        clean = line.replace("**", "").strip()
        if clean.startswith("SEVERITY:"):
            severity = clean.replace("SEVERITY:", "").strip().upper()
            if severity in SEVERITY_COLORS:
                return severity
    return "LOW"

def print_report(reviews: list):
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]CodeGuard Review Report[/bold cyan]",
        box=box.DOUBLE
    ))

    for item in reviews:
        filename = item["file"]
        review = item["review"]
        severity = parse_severity(review)
        color = SEVERITY_COLORS.get(severity, "white")

        console.print(f"\n[bold {color}]📄 {filename} — {severity}[/bold {color}]")
        console.print(Panel(
            review,
            border_style=color,
            box=box.SIMPLE
        ))

    console.print(f"\n[bold green]✅ Review complete. {len(reviews)} file(s) reviewed.[/bold green]\n")