"""Textual-based wizard UI for fishy-config."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Static, Switch, TextArea

from .wizard import (
    field_examples,
    get_field_default,
    normalize_prompt_seed,
    parse_prompt_value,
    stringify_default,
    MISSING,
)
from .style import CSS

@dataclass
class WizardFieldSpec:
    """Single field to collect from the user."""

    name: str
    label: str
    title: str
    description: str | None
    examples: list[str]
    default: Any
    kind: Literal["text", "bool"]
    advanced: bool

@dataclass
class WizardSetup:
    """Top-level wizard options collected before prompting the model fields."""

    config_dir: Path | None
    dest_dir: Path | None
    strict_undefined: bool
    dry_run: bool
    overwrite: bool
    clean_dest: bool
    skip_patterns: list[str] = field(default_factory=list)


@dataclass
class WizardResult:
    """Collected wizard output returned to the CLI layer."""

    config_dir: Path
    dest_dir: Path
    context: dict[str, Any]
    strict_undefined: bool
    dry_run: bool
    overwrite: bool
    clean_dest: bool
    skip_patterns: list[str]


@dataclass
class StepResult:
    """Small result object returned by individual screens."""

    action: Literal["next", "back", "cancel", "render"]
    value: Any = None


@dataclass
class BuildSession:
    """Mutable state shared by the wizard screens."""

    setup: WizardSetup
    field_specs: list[WizardFieldSpec]
    context: dict[str, Any] = field(default_factory=dict)


def build_field_specs(
    context_model: type[BaseModel], seed_context: dict[str, Any]
) -> list[WizardFieldSpec]:
    """Create prompt specs from a Pydantic context model."""

    specs: list[WizardFieldSpec] = []
    for field_name, field_info in context_model.model_fields.items():
        default = seed_context.get(field_name, get_field_default(field_info))
        default = normalize_prompt_seed(default)
        title = field_info.title or field_info.alias or field_name
        if title.startswith("&"):
            title = title[1:]
            advanced = True
        else:
            advanced = False
        specs.append(
            WizardFieldSpec(
                name=field_name,
                label=field_info.alias or field_name,
                title=title,
                advanced=advanced,
                description=field_info.description,
                examples=[str(example) for example in field_examples(field_info)],
                default=default,
                kind="bool" if field_info.annotation is bool else "text",
            )
        )
    return specs


class WizardApp(App[None]):
    """Textual app that walks the user through render setup."""

    BINDINGS = [("escape", "cancel", "Cancel")]
    CSS = CSS
    TITLE = "fishy-config - Configuration Wizard"

    def __init__(self, session: BuildSession):
        super().__init__()
        self.session = session
        self._field_index = 0
        self.result: WizardResult | None = None

    def on_mount(self) -> None:
        self.push_screen(SetupScreen(self.session.setup), self._handle_setup_result)

    def action_cancel(self) -> None:
        self.exit()

    def _handle_setup_result(self, outcome: StepResult | None) -> None:
        if outcome is None or outcome.action == "cancel":
            self.exit()
            return

        setup = outcome.value
        assert isinstance(setup, WizardSetup)
        self.session.setup = setup
        self.session.context = dict(self.session.context)
        self._field_index = 0
        self._push_next_field_or_summary()

    def _push_next_field_or_summary(self) -> None:
        if self._field_index >= len(self.session.field_specs):
            self.push_screen(SummaryScreen(self.session), self._handle_summary_result)
            return

        spec = self.session.field_specs[self._field_index]
        current_value = self.session.context.get(spec.name, spec.default)
        self.push_screen(
            FieldScreen(spec, self._field_index + 1, len(self.session.field_specs), current_value),
            self._handle_field_result,
        )

    def _handle_field_result(self, outcome: StepResult | None) -> None:
        if outcome is None or outcome.action == "cancel":
            self.exit()
            return

        if outcome.action == "back":
            previous_index = self._field_index - 1
            if previous_index < 0:
                self.push_screen(SetupScreen(self.session.setup), self._handle_setup_result)
                return
            self._field_index = previous_index
            self._push_next_field_or_summary()
            return

        spec = self.session.field_specs[self._field_index]
        self.session.context[spec.name] = outcome.value
        self._field_index += 1
        self._push_next_field_or_summary()

    def _handle_summary_result(self, outcome: StepResult | None) -> None:
        if outcome is None or outcome.action == "cancel":
            self.exit()
            return

        if outcome.action == "back":
            if not self.session.field_specs:
                self.push_screen(SetupScreen(self.session.setup), self._handle_setup_result)
                return
            self._field_index = len(self.session.field_specs) - 1
            self._push_next_field_or_summary()
            return

        setup = self.session.setup
        self.result = WizardResult(
            config_dir=setup.config_dir,
            dest_dir=setup.dest_dir,
            context=dict(self.session.context),
            strict_undefined=setup.strict_undefined,
            dry_run=setup.dry_run,
            overwrite=setup.overwrite,
            clean_dest=setup.clean_dest,
            skip_patterns=list(setup.skip_patterns),
        )
        self.exit()


class SetupScreen(Screen[StepResult]):
    """Collect high-level render settings before prompting context fields."""

    def __init__(self, setup: WizardSetup):
        super().__init__()
        self.setup = setup

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="card"):
            yield Static("Render Options", classes="title")
            yield Static("Options for rendering. These should be left default most of the time.", classes="muted")

            with Horizontal(classes="button-row"):
                yield Button("Cancel", variant="default", id="cancel")
                yield Button("Skip", variant="primary", id="continue")
            
            yield Static("Advanced options", classes="title")

            yield Static("Source directory", classes="field-label")
            yield Input(
                value=self._path_value(self.setup.config_dir),
                id="config-dir",
                classes="value-input",
            )
            yield Static("The directory containing your config templates.", classes="field-description")
                
            yield Static("Destination directory", classes="field-label")
            yield Input(
                value=self._path_value(self.setup.dest_dir), id="dest-dir", classes="value-input"
            )
            yield Static("The directory where the rendered config files will be saved.", classes="field-description")

            yield Static("Strict undefined", classes="field-label")
            yield Switch(value=self.setup.strict_undefined, id="strict-undefined")
            yield Static(f"Whether to error on undefined variables in templates. Default: {'yes' if self.setup.strict_undefined else 'no'}", classes="field-description")

            yield Static("Dry run", classes="field-label")
            yield Switch(value=self.setup.dry_run, id="dry-run")
            yield Static(f"Whether to perform a dry run without writing files. Default: {'yes' if self.setup.dry_run else 'no'}", classes="field-description")

            yield Static("Overwrite existing files", classes="field-label")
            yield Switch(value=self.setup.overwrite, id="overwrite")
            yield Static(f"Whether to overwrite existing files during rendering. Default: {'yes' if self.setup.overwrite else 'no'}", classes="field-description")

            yield Static("Clean destination first", classes="field-label")
            yield Switch(value=self.setup.clean_dest, id="clean-dest")
            yield Static(f"Whether to delete existing files in the destination directory before rendering. Default: {'yes' if self.setup.clean_dest else 'no'}", classes="field-description")

            yield Static("Skip patterns (comma-separated)", classes="field-label")
            yield Input(
                value=", ".join(self.setup.skip_patterns),
                id="skip-patterns",
                classes="value-input",
            )
            yield Static("File patterns to skip during rendering (e.g. 'secrets.yaml, *.tmp').", classes="field-description")

            with Horizontal(classes="button-row"):
                yield Button("Cancel", variant="default", id="cancel")
                yield Button("Continue", variant="primary", id="continue")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#config-dir", Input).focus()

    def _path_value(self, value: Path | None) -> str:
        return "" if value is None else str(value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "cancel":
            self.dismiss(StepResult("cancel"))
            return

        config_dir = self.query_one("#config-dir", Input).value.strip()
        dest_dir = self.query_one("#dest-dir", Input).value.strip()
        if not config_dir or not dest_dir:
            self.notify(
                "Config directory and destination directory are required.", severity="error"
            )
            return

        skip_patterns = _parse_skip_patterns(self.query_one("#skip-patterns", Input).value)
        self.dismiss(
            StepResult(
                "next",
                WizardSetup(
                    config_dir=Path(config_dir),
                    dest_dir=Path(dest_dir),
                    strict_undefined=self.query_one("#strict-undefined", Switch).value,
                    dry_run=self.query_one("#dry-run", Switch).value,
                    overwrite=self.query_one("#overwrite", Switch).value,
                    clean_dest=self.query_one("#clean-dest", Switch).value,
                    skip_patterns=skip_patterns,
                ),
            )
        )


class FieldScreen(Screen[StepResult]):
    """Prompt for one context field."""

    def __init__(self, spec: WizardFieldSpec, position: int, total: int, current_value: Any):
        super().__init__()
        self.spec = spec
        self.position = position
        self.total = total
        self.current_value = current_value

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="card"):
            yield Static(f"Context field {self.position}/{self.total} - {self.spec.label}", classes="muted")
            yield Static(self.spec.title, classes="title")
            if self.spec.description:
                yield Static(self.spec.description, classes="muted")
            if self.spec.examples:
                yield Static(f"Examples: {', '.join(self.spec.examples)}", classes="muted")

            if self.spec.kind == "bool":
                yield Switch(value=bool(self._initial_bool_value()), id="value")
            else:
                yield Static("Enter a YAML-compatible value.", classes="field-label")
                yield TextArea(
                    text=(
                        ""
                        if self.current_value is MISSING
                        else stringify_default(self.current_value)
                    ),
                    id="value",
                    classes="value-input",
                )

            with Horizontal(classes="button-row"):
                yield Button("Back", variant="default", id="back")
                yield Button("Next", variant="primary", id="next")
        yield Footer()

    def on_mount(self) -> None:
        if self.spec.kind == "text":
            self.query_one("#value", TextArea).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "back":
            self.dismiss(StepResult("back"))
            return
        if button_id == "next":
            if self.spec.kind == "bool":
                value = self.query_one("#value", Switch).value
            else:
                raw_value = self.query_one("#value", TextArea).text.strip()
                if not raw_value and self.current_value is MISSING:
                    self.notify(f"{self.spec.label} is required.", severity="error")
                    return
                value = self.current_value if not raw_value else parse_prompt_value(raw_value)
            self.dismiss(StepResult("next", value))

    def _initial_bool_value(self) -> bool:
        if self.current_value is MISSING:
            return False
        return bool(self.current_value)


class SummaryScreen(Screen[StepResult]):
    """Present a final summary before running the render pipeline."""

    def __init__(self, session: BuildSession):
        super().__init__()
        self.session = session

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="card"):
            yield Static("Summary", classes="title")
            yield Static("Review the collected configuration before rendering. Use the Back button to make changes.", classes="muted")
            summary = {
                "config_dir": str(self.session.setup.config_dir),
                "dest_dir": str(self.session.setup.dest_dir),
                "strict_undefined": self.session.setup.strict_undefined,
                "dry_run": self.session.setup.dry_run,
                "overwrite": self.session.setup.overwrite,
                "clean_dest": self.session.setup.clean_dest,
                "skip_patterns": self.session.setup.skip_patterns,
                "context": self.session.context,
            }
            yield Static(yaml.safe_dump(summary, sort_keys=True).rstrip())

            with Horizontal(classes="button-row"):
                yield Button("Back", variant="default", id="back")
                yield Button("Cancel", variant="default", id="cancel")
                yield Button("Render", variant="primary", id="render")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "back":
            self.dismiss(StepResult("back"))
            return
        if button_id == "cancel":
            self.dismiss(StepResult("cancel"))
            return
        if button_id == "render":
            self.dismiss(StepResult("render"))


def run_wizard_tui(session: BuildSession) -> WizardResult | None:
    """Run the wizard TUI and return the collected values."""

    app = WizardApp(session)
    app.run()
    return app.result


def _parse_skip_patterns(raw_value: str) -> list[str]:
    if not raw_value.strip():
        return []

    return [pattern.strip() for pattern in raw_value.split(",") if pattern.strip()]
