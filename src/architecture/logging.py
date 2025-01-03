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
                f"[cyan]{logging.Formatter().formatTime(record)}[/cyan] | "
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


class LoggerFactory:
    @staticmethod
    def create(name: str) -> logging.Logger:
        """
        Cria um logger configurado para o app.

        Args:
            name (str): Nome do logger.

        Returns:
            logging.Logger: Instância do logger configurado.
        """
        logger = logging.getLogger(name)

        # Here we set the logger level to NOTSET by default,
        # which allows all messages to flow (DEBUG, INFO, etc.).
        logger.setLevel(logging.NOTSET)

        # Avoid duplicate handlers if logger already exists
        if not logger.handlers:
            # Create Rich handler
            rich_handler = RichHandler()
            rich_handler.setLevel(logging.NOTSET)
            rich_handler.setFormatter(
                logging.Formatter("%(levelname)-8s | %(asctime)s | %(message)s")
            )

            # Add Rich handler to logger
            logger.addHandler(rich_handler)

        return logger


# Use LoggerFactory to create a logger instance
logger = LoggerFactory.create("global")
