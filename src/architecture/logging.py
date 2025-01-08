"""Módulo de configuração de logging do app"""

from __future__ import annotations

import logging
from rich.console import Console
from rich.theme import Theme
from rich.traceback import install as install_rich_traceback

# Install rich traceback handling
install_rich_traceback(show_locals=False)


class RichHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level_name = record.levelname.lower()
            level_color = level_name

            log_message = (
                f"[{level_color}]{record.levelname:<8}[/{level_color}] | "
                f"[cyan]{self.formatTime(record)}[/cyan] | "
                f"[{level_color}]{record.getMessage()}[/{level_color}]"
            )

            console = Console(
                theme=Theme(
                    {
                        "debug": "dim cyan",
                        "info": "bold cyan",
                        "success": "bold green",
                        "warning": "bold yellow",
                        "error": "bold red",
                        "critical": "bold white on red",
                    }
                )
            )

            console.print(log_message, markup=True)

            # Print the exception traceback if any
            if record.exc_info:
                console.print_exception(
                    show_locals=False, width=100, extra_lines=3, word_wrap=True
                )
        except Exception:
            self.handleError(record)

    def formatTime(self, record, datefmt=None):
        return logging.Formatter("%(asctime)s").formatTime(record, datefmt)


class LoggerFactory:
    @staticmethod
    def create(name: str, level: int = logging.DEBUG) -> logging.Logger:
        """
        Creates a beautiful and rich logger for the application.

        Args:
            name (str): Nome do logger.
            level (int, optional): Nível de log para o logger. Defaults to logging.DEBUG.

        Returns:
            logging.Logger: Instância do logger configurado.
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)  # Set logger level using parameter

        if not logger.handlers:
            rich_handler = RichHandler()
            rich_handler.setLevel(logging.DEBUG)  # Set handler level
            logger.addHandler(rich_handler)

        return logger


# Use LoggerFactory to create a logger instance
logger = LoggerFactory.create("global")  # Level is DEBUG by default
