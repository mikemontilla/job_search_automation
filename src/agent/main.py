import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.spinner import Spinner
from rich.live import Live

from src.agent.agent import JobAgent
from src.agent.session import load_session
from src.agent.prompts import session_start_prompt

console = Console()


def print_agent(text: str) -> None:
    console.print(Panel(Markdown(text), border_style="blue", padding=(1, 2)))


def print_user(text: str) -> None:
    console.print(f"[bold green]You:[/bold green] {text}\n")


def run() -> None:
    console.print(Panel(
        "[bold blue]Job Search Agent[/bold blue]\n"
        "[dim]Type your message and press Enter. Type [bold]exit[/bold] or press Ctrl+C to quit.[/dim]",
        border_style="blue",
    ))

    _, last_note = load_session()
    agent = JobAgent()

    # Proactive session-start message
    start_prompt = session_start_prompt(last_note)
    with Live(Spinner("dots", text="[dim]Thinking...[/dim]"), console=console, transient=True):
        response = agent.chat(start_prompt)
    print_agent(response)

    # Main conversation loop
    while True:
        try:
            user_input = Prompt.ask("[bold green]You[/bold green]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]")
            sys.exit(0)

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "bye"):
            console.print("[dim]Goodbye![/dim]")
            sys.exit(0)

        with Live(Spinner("dots", text="[dim]Thinking...[/dim]"), console=console, transient=True):
            response = agent.chat(user_input)

        print_agent(response)


if __name__ == "__main__":
    run()
