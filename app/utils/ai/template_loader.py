"""
Template loader utility for AI prompt templates.
Provides a centralized way to load and render Jinja2 templates for LLM prompts.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape


class TemplateLoader:
    """Manages loading and rendering of Jinja2 templates for AI prompts."""

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize the template loader.

        Args:
            template_dir: Path to the templates directory. If None, uses the default location.
        """
        if template_dir is None:
            # Get the directory where this file is located
            current_dir = Path(__file__).parent
            template_dir = current_dir / "templates"

        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def get_template(self, template_name: str) -> Template:
        """
        Get a template by name.

        Args:
            template_name: Name of the template file (e.g., 'debugging_prompt.j2')

        Returns:
            The loaded template object

        Raises:
            jinja2.TemplateNotFound: If the template doesn't exist
        """
        return self.env.get_template(template_name)

    def render(self, template_name: str, **context: Any) -> str:
        """
        Render a template with the given context.

        Args:
            template_name: Name of the template file
            **context: Variables to pass to the template

        Returns:
            The rendered template string
        """
        template = self.get_template(template_name)
        return template.render(**context)

    def list_templates(self) -> list[str]:
        """
        List all available templates in the template directory.

        Returns:
            List of template filenames
        """
        return self.env.list_templates()


# Create a singleton instance for convenience
_default_loader: Optional[TemplateLoader] = None


def get_template_loader() -> TemplateLoader:
    """
    Get the default template loader instance.

    Returns:
        The default template loader
    """
    global _default_loader
    if _default_loader is None:
        _default_loader = TemplateLoader()
    return _default_loader


def render_template(template_name: str, **context: Any) -> str:
    """
    Convenience function to render a template using the default loader.

    Args:
        template_name: Name of the template file
        **context: Variables to pass to the template

    Returns:
        The rendered template string
    """
    loader = get_template_loader()
    return loader.render(template_name, **context)
