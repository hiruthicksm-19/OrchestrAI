"""
DebateAI — Terminal Entrypoint.

Run from the backend/ directory:
    python main.py

This is the Phase 1 CLI interface. Phase 2 will add a FastAPI server.
"""

from __future__ import annotations

import asyncio
import sys

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
from rich import box

from app.core.settings import Settings
from app.debate.debate_engine import DebateEngine
from app.debate.debate_state import DebateResult, DebateState
from app.utils.exceptions import DebateAIError
from app.utils.logger import get_logger

logger = get_logger(__name__)
console = Console()


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _print_banner() -> None:
    console.print()
    console.print(Panel(
        Text("DebateAI  •  Multi-Agent Adversarial Debate", justify="center", style="bold cyan"),
        subtitle="[dim]Phase 1 — Terminal Mode[/dim]",
        box=box.DOUBLE_EDGE,
        border_style="cyan",
    ))
    console.print()


def _print_strategy_header(result: DebateResult) -> None:
    """Show what strategy was selected before the debate output."""
    state: DebateState = result.state
    res_pos = state.metadata.get("research_position", "primary position")
    opp_pos = state.metadata.get("opponent_position", "opposing position")

    console.print(Panel(
        f"[bold]Type:[/bold]     [yellow]{result.question_type}[/yellow]\n"
        f"[bold]Strategy:[/bold] [yellow]{result.debate_strategy}[/yellow]\n"
        f"[bold]Research:[/bold] [green]{res_pos}[/green]\n"
        f"[bold]Opponent:[/bold] [red]{opp_pos}[/red]",
        title="[dim]Debate Configuration[/dim]",
        border_style="dim",
        padding=(0, 2),
    ))
    console.print()


def _print_opening_statements(result: DebateResult) -> None:
    if not result.rounds:
        return

    round_data = result.rounds[0]
    console.print(Rule("[bold yellow]Opening Statements[/bold yellow]"))

    if round_data.research_response:
        console.print(Panel(
            round_data.research_response,
            title="[bold green]Research Agent[/bold green]",
            border_style="green",
            padding=(1, 2),
        ))

    if round_data.critical_response:
        console.print(Panel(
            round_data.critical_response,
            title="[bold red]Opponent Agent[/bold red]",
            border_style="red",
            padding=(1, 2),
        ))


def _print_rebuttals(result: DebateResult) -> None:
    if not result.research_rebuttal and not result.critical_rebuttal:
        return

    console.print(Rule("[bold yellow]Rebuttals[/bold yellow]"))

    if result.research_rebuttal:
        console.print(Panel(
            result.research_rebuttal,
            title="[bold green]Research Agent — Rebuttal[/bold green]",
            border_style="green",
            padding=(1, 2),
        ))

    if result.critical_rebuttal:
        console.print(Panel(
            result.critical_rebuttal,
            title="[bold red]Opponent Agent — Rebuttal[/bold red]",
            border_style="red",
            padding=(1, 2),
        ))


def _print_consensus(result: DebateResult) -> None:
    console.print(Rule("[bold cyan]Final Answer[/bold cyan]"))
    console.print(Panel(
        result.consensus,
        title="[bold cyan]Consensus Agent[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    ))
    console.print()

    state: DebateState = result.state
    msg_count = len(state.messages) if state else 0
    latencies = [f"{m.latency_ms:.0f}ms" for m in state.messages] if state else []

    console.print(
        f"[dim]Strategy: {result.debate_strategy}  •  "
        f"{msg_count} agent calls  •  "
        f"Total: {result.duration_seconds:.1f}s[/dim]"
    )
    if latencies:
        console.print(f"[dim]Latencies: {' | '.join(latencies)}[/dim]")
    console.print()


# ---------------------------------------------------------------------------
# Main debate loop
# ---------------------------------------------------------------------------

async def run_debate(question: str, settings: Settings) -> None:
    """Run a single debate and print results to the terminal."""
    engine = DebateEngine(settings=settings)

    with console.status("[bold cyan]Debate in progress…[/bold cyan]", spinner="dots"):
        result = await engine.run(question)

    _print_strategy_header(result)

    has_opponent = bool(result.rounds and result.rounds[0].critical_response)
    if has_opponent:
        _print_opening_statements(result)
        _print_rebuttals(result)

    _print_consensus(result)


async def main() -> None:
    """Interactive terminal loop."""
    _print_banner()

    try:
        settings = Settings()
    except Exception as exc:
        console.print(f"[bold red]Configuration error:[/bold red] {exc}")
        sys.exit(1)

    console.print("[dim]Agents: Research (Groq) • Opponent (OpenAI) • Consensus (Mistral)[/dim]")
    console.print("[dim]Strategy adapts automatically to question type.[/dim]\n")

    while True:
        try:
            question = console.input(
                "[bold white]Enter your question[/bold white] [dim](or 'quit' to exit)[/dim]: "
            ).strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if not question:
            console.print("[yellow]Please enter a question.[/yellow]")
            continue

        if question.lower() in {"quit", "exit", "q"}:
            console.print("[dim]Goodbye.[/dim]")
            break

        console.print()
        console.print(Panel(
            f"[bold]{question}[/bold]",
            title="[dim]Question[/dim]",
            border_style="dim",
            padding=(0, 2),
        ))
        console.print()

        try:
            await run_debate(question=question, settings=settings)
        except DebateAIError as exc:
            console.print(f"\n[bold red]Debate error:[/bold red] {exc}\n")
        except Exception as exc:
            logger.exception("Unexpected error during debate")
            console.print(f"\n[bold red]Unexpected error:[/bold red] {exc}\n")


if __name__ == "__main__":
    asyncio.run(main())
