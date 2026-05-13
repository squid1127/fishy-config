"""Stylesheet for the Textual-based interactive configuration wizard."""

CSS = """
    Screen {
        align: center middle;
        background: $surface;
    }

    #card {
        width: 90%;
        max-width: 96;
        height: auto;
        border: round $accent;
        padding: 1 2;
        background: $panel;
    }

    .title {
        text-style: bold;
        margin-bottom: 1;
    }
    
    .muted {
        color: $text-muted;
        margin-bottom: 1;
    }

    .field-label {
        margin-top: 1;
    }
    .field-description {
        color: $text-muted;
        margin-top: 0;
        margin-bottom: 1;
    }

    .value-input {
        margin-top: 0;
        margin-bottom: 0;
    }

    .button-row {
        height: auto;
        margin-top: 1;
        margin-bottom: 1;
    }
    
    """