"""Constants for running analyses through the local Claude Code CLI."""

from __future__ import annotations


class ClaudeCliSettings:
    """Executable lookup, timeout and the fixed headless flags."""

    PATH_ENV_VAR = "FINANMIND_CLAUDE_CLI_PATH"
    EXECUTABLE_NAME = "claude"
    NPM_NATIVE_BINARY = ("node_modules", "@anthropic-ai", "claude-code", "bin", "claude.exe")
    TIMEOUT_SECONDS = 300.0
    MODEL_PATTERN = r"^[A-Za-z0-9._\-\[\]]*$"
    # Headless, no tools, no MCP, no saved session: the CLI only answers the prompt.
    HEADLESS_FLAGS = (
        "-p",
        "--output-format", "json",
        "--tools", "",
        "--no-session-persistence",
        "--disable-slash-commands",
        "--strict-mcp-config",
    )
    JSON_ONLY_SUFFIX = (
        "\n\nResponde únicamente con el objeto JSON solicitado, sin texto adicional "
        "y sin bloques de código markdown."
    )
