"""
Interactive REPL mode for the agent.

Simple terminal interface for interactive use.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()


class InteractiveREPL:
    """
    Simple interactive REPL for agent.

    Usage:
        repl = InteractiveREPL(agent)
        repl.run()
    """

    def __init__(self, agent, output_dir: Optional[Path] = None):
        self.agent = agent
        self.output_dir = output_dir or Path.home() / ".swe-agent" / "runs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def print_banner(self):
        """Print welcome banner."""
        console.print(Panel.fit(
            "[bold blue]SWE Agent v2[/bold blue]\n"
            "[dim]Conductor + FunctionGemma Ring[/dim]\n\n"
            "Commands:\n"
            "  [green]/quit[/green]  - Exit\n"
            "  [green]/cost[/green]  - Show cost\n"
            "  [green]/clear[/green] - Clear history",
            title="Welcome",
        ))

    def print_cost(self):
        """Print current cost."""
        if hasattr(self.agent, 'history'):
            h = self.agent.history
            console.print(f"[dim]Steps: {h.n_steps} | "
                         f"Tokens: {h.total_tokens} | "
                         f"Cost: ${h.total_cost:.4f}[/dim]")

    def get_task(self) -> Optional[str]:
        """Get task from user."""
        console.print("\n[bold yellow]What would you like me to do?[/bold yellow]")
        console.print("[dim]Enter task (Ctrl+D or /quit to exit):[/dim]")

        lines = []
        try:
            while True:
                line = input()
                if line.strip() == "/quit":
                    return None
                if line.strip() == "":
                    if lines:
                        break
                    continue
                lines.append(line)
        except EOFError:
            if not lines:
                return None

        return "\n".join(lines)

    def run(self):
        """Run the REPL loop."""
        self.print_banner()

        while True:
            task = self.get_task()
            if task is None:
                console.print("[yellow]Goodbye![/yellow]")
                break

            if task.startswith("/"):
                self.handle_command(task)
                continue

            console.print(f"\n[bold green]Working on:[/bold green] {task[:100]}...")
            console.print("[dim]This may take a moment...[/dim]\n")

            try:
                # Run agent
                if asyncio.iscoroutinefunction(self.agent.solve):
                    result = asyncio.run(self.agent.solve(task))
                else:
                    result = self.agent.solve(task)

                # Display result
                console.print(Panel(
                    Markdown(result) if "```" in result else result,
                    title="[green]Result[/green]",
                    border_style="green",
                ))

            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

            self.print_cost()

    def handle_command(self, cmd: str):
        """Handle REPL commands."""
        cmd = cmd.lower().strip()

        if cmd == "/quit":
            return  # Handled in get_task

        elif cmd == "/cost":
            self.print_cost()

        elif cmd == "/clear":
            if hasattr(self.agent, 'history'):
                self.agent.history = type(self.agent.history)()
            console.print("[dim]History cleared[/dim]")

        elif cmd == "/help":
            self.print_banner()

        else:
            console.print(f"[red]Unknown command: {cmd}[/red]")


def run_interactive(agent):
    """Convenience function to run interactive mode."""
    repl = InteractiveREPL(agent)
    repl.run()
