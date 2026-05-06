"""Application entry point."""

from finanmind.ui.desktop_runner import DesktopRunner


class Application:
    """Bootstraps and runs the Finanmind desktop GUI."""

    @classmethod
    def run(cls) -> None:
        """Start the desktop application (GUI bootstrap goes here)."""
        runner = DesktopRunner()
        runner.run()


if __name__ == "__main__":
    Application.run()
