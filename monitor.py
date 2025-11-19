"""
Enhanced monitoring tool for YouTube Watcher
Shows real-time verification of video watching
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich import box
import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

console = Console()


class WatcherMonitor:
    """Real-time monitor for watcher verification"""

    def __init__(self, api_url: str = "http://localhost:5001"):
        self.api_url = api_url
        self.running = False
        self.last_status = None
        self.verification_data = {}

    async def fetch_status(self) -> Optional[dict]:
        """Fetch current status from API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/api/status") as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            logger.debug(f"Error fetching status: {e}")
        return None

    def create_verification_table(self, status: dict) -> Table:
        """Create table showing video watching verification"""
        table = Table(title="Video Watching Verification", box=box.ROUNDED)

        table.add_column("ID", style="cyan", width=6)
        table.add_column("Status", width=12)
        table.add_column("Iteration", style="yellow", width=10)
        table.add_column("Video Progress", width=40)
        table.add_column("Verification", width=15)
        table.add_column("Current Action", width=30)

        watchers = status.get('watchers', [])

        for watcher in watchers:
            watcher_id = str(watcher.get('id', '-'))
            status_text = watcher.get('status', 'unknown')
            iteration = f"#{watcher.get('iteration', 0)}"
            progress = watcher.get('progress', 0)
            message = watcher.get('message', '-')

            # Determine verification status
            if 'watching' in message.lower() or 'video watched' in message.lower():
                verification = "✓ WATCHING"
                verification_style = "green"
            elif 'completed' in message.lower():
                verification = "✓ COMPLETE"
                verification_style = "green"
            elif 'failed' in message.lower():
                verification = "✗ FAILED"
                verification_style = "red"
            elif 'error' in message.lower():
                verification = "✗ ERROR"
                verification_style = "red"
            elif 'starting' in message.lower():
                verification = "⋯ STARTING"
                verification_style = "yellow"
            else:
                verification = "⋯ IDLE"
                verification_style = "dim"

            # Create progress bar
            bar_length = 20
            filled = int(bar_length * progress / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            progress_text = f"{bar} {progress}%"

            # Status color
            status_colors = {
                'running': 'green',
                'completed': 'blue',
                'error': 'red',
                'cancelled': 'yellow',
                'stopped': 'dim'
            }
            status_style = status_colors.get(status_text, 'white')

            table.add_row(
                watcher_id,
                f"[{status_style}]{status_text}[/{status_style}]",
                iteration,
                progress_text,
                f"[{verification_style}]{verification}[/{verification_style}]",
                message[:30]
            )

        if not watchers:
            table.add_row("-", "No watchers running", "-", "-", "-", "-")

        return table

    def create_summary_panel(self, status: dict) -> Panel:
        """Create summary panel"""
        is_running = status.get('is_running', False)
        total = status.get('total_watchers', 0)
        successful = status.get('successful', 0)
        failed = status.get('failed', 0)
        elapsed = status.get('elapsed_seconds', 0)

        if elapsed:
            elapsed_str = f"{int(elapsed // 3600)}h {int((elapsed % 3600) // 60)}m {int(elapsed % 60)}s"
        else:
            elapsed_str = "Not started"

        summary = f"""
[bold]System Status:[/bold] {'🟢 RUNNING' if is_running else '🔴 STOPPED'}
[bold]Total Watchers:[/bold] {total}
[bold]Successful Runs:[/bold] [green]{successful}[/green]
[bold]Failed Runs:[/bold] [red]{failed}[/red]
[bold]Success Rate:[/bold] {(successful / (successful + failed) * 100 if (successful + failed) > 0 else 0):.1f}%
[bold]Elapsed Time:[/bold] {elapsed_str}
        """

        return Panel(summary, title="📊 Overview", border_style="blue")

    def create_error_log_panel(self, status: dict) -> Panel:
        """Create error log panel"""
        watchers = status.get('watchers', [])
        errors = []

        for watcher in watchers:
            if 'error' in watcher.get('status', '').lower() or 'failed' in watcher.get('message', '').lower():
                errors.append(f"Watcher #{watcher['id']}: {watcher.get('message', 'Unknown error')}")

        if errors:
            error_text = "\n".join(errors[:5])  # Show last 5 errors
            style = "red"
        else:
            error_text = "No errors detected ✓"
            style = "green"

        return Panel(error_text, title="⚠️ Error Log", border_style=style)

    def create_layout(self, status: dict) -> Layout:
        """Create dashboard layout"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=10),
            Layout(name="main"),
            Layout(name="footer", size=8)
        )

        layout["header"].update(self.create_summary_panel(status))
        layout["main"].update(self.create_verification_table(status))
        layout["footer"].update(self.create_error_log_panel(status))

        return layout

    async def monitor_loop(self):
        """Main monitoring loop"""
        self.running = True

        with Live(console=console, refresh_per_second=2) as live:
            while self.running:
                try:
                    status = await self.fetch_status()

                    if status:
                        self.last_status = status
                        layout = self.create_layout(status)
                        live.update(layout)
                    else:
                        live.update(Panel(
                            "[red]Cannot connect to YouTube Watcher API[/red]\n"
                            "Make sure the server is running at http://localhost:5001",
                            title="Connection Error"
                        ))

                    await asyncio.sleep(2)  # Update every 2 seconds

                except KeyboardInterrupt:
                    self.running = False
                    break
                except Exception as e:
                    logger.error(f"Monitor error: {e}")
                    await asyncio.sleep(2)

    def stop(self):
        """Stop monitoring"""
        self.running = False


async def main():
    """Run monitor"""
    console.print("[bold green]YouTube Watcher Monitor[/bold green]")
    console.print("Starting real-time monitoring...\n")

    monitor = WatcherMonitor()

    try:
        await monitor.monitor_loop()
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped[/yellow]")
    finally:
        monitor.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
