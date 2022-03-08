from pathlib import Path

from rich.prompt import PromptBase


class PathPrompt(PromptBase[Path]):
    """A prompt that returns an integer.
    Example:
        >>> x_marks_the_spot = PathPrompt.ask("Where did you store the treasure ?")
    """
    response_type = Path
    validate_error_message = "[prompt.invalid]Please enter a valid path"
