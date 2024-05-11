from typing import Any, Callable, Dict, List, Optional
import click
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from prompt_toolkit.validation import Validator, ValidationError
from safe.database import Credential, Database

STATUS_COLORS = {
    'error': 'red',
    'info': 'cyan',
    'success': 'green',
    'warning': 'yellow'
}

STATUS_SYMBOLS = {
    'error': '✗',
    'info': 'i',
    'success': '✓',
    'warning': '!'
}


class CredentialNameValidator(Validator):
    """Prompt validator for credential name.

    Args:
        validator_cb: Any function that checks the existence of the credential
            name in the database.
        allow: Allowed name even if it already exists in the database.
    """

    def __init__(
        self,
        validator_cb: Callable[[str], bool],
        allow: Optional[str] = None
    ):
        self.validator_cb = validator_cb
        self.allow = allow

    def validate(self, document):
        text = document.text.strip()

        if not text:
            raise ValidationError(
                message='The prompt is empty.',
                cursor_position=document.cursor_position
            )

        if text != self.allow and self.validator_cb(text):
            raise ValidationError(
                message=f'{text} already exists in the database.',
                cursor_position=document.cursor_position
            )


class ItemKeyValidator(Validator):
    """Prompt validator for item key.

    Args:
        items: Credential items in key-value pair.
    """

    def __init__(self, items: Dict[str, str], allow_empty: Optional[bool] = False):
        self.items = items
        self.allow_empty = allow_empty

    def validate(self, document):
        text = document.text.strip()

        if text in self.items:
            raise ValidationError(
                message=f'{text} is already in-use.',
                cursor_position=document.cursor_position
            )

        if not text and len(self.items) == 0 and not self.allow_empty:
            raise ValidationError(
                message=f'Must add atleast 1 key-value pair.',
                cursor_position=document.cursor_position
            )


def print_status(
    message: str,
    type_: str = 'info',
    start: str = '',
    end: str = '',
    concise: bool = True,
    **kwargs
) -> None:
    """Prints a status message.

    Args:
        message: Status message
        type_: Status type (error, info, success, warning)
        start: Character[s] before the status message.
        end: Character[s] after the status message.
        concise: Prints a simple status message.
    """
    if concise:
        click.echo('{}{} {}{}'.format(
            start,
            click.style(STATUS_SYMBOLS[type_], fg=STATUS_COLORS[type_]),
            message,
            end
        ), **kwargs)
    else:
        click.echo('{}{} {}{}'.format(
            start,
            click.style(f'{type_.upper()}:',
                        fg=STATUS_COLORS[type_], bold=True),
            click.style(message, fg=STATUS_COLORS[type_]),
            end
        ), **kwargs)


def print_credentials(
    credentials: List[Dict[str, Any]] | Dict[str, Any],
    pager: bool = False,
    start: str = '',
    end: str = ''
) -> None:
    """Prints credential[s] to stdout or pager.

    Args:
        credentials: List of credential or a single credential.

    Example:
        >>> from safe.utils import print_credentials
        ... print_credentials({
        ...     'name': 'Account',
        ...     'items': {
        ...         'Username': 'example',
        ...         'Password': 'example123'
        ...     }
        ... })
        [Account]
          Username = example
          Password = example123
    """
    if type(credentials) != list:
        credentials = [credentials]

    creds_str = start
    for credential in credentials:
        name, items = credential.values()
        max_key_length = len(max(items, key=len))
        # Not to be confused with creds_str
        cred_str = f'[{name}]\n'

        for key, value in items.items():
            cred_str += '  {}{} = {}\n'.format(
                key,
                (max_key_length - len(key)) * ' ',
                click.style(value or '[empty]', fg='blue')
            )

        creds_str += cred_str
        if name != credentials[-1]['name']:
            creds_str += '\n'
        else:
            creds_str += end

    if pager:
        click.echo_via_pager(creds_str)
    else:
        click.echo(creds_str, nl=False)


def pick_credential(db: Database, name: Optional[str]) -> Optional[Credential]:
    """Prompt for picking credential.

    Args:
        name: Name of the credential.
    """
    if not db.exists(name):
        if name:
            click.echo(
                f"{click.style(name, bold=True)} doesn't exists in the database.")
            click.echo('Pick another instead:\n')

        credentials = db.get_all()
        picked_index = inquirer.rawlist(
            message='Pick a credential',
            choices=[Choice(name=credential.name, value=i)
                     for i, credential in enumerate(credentials)]
        ).execute()
        click.echo()
        return credentials[picked_index]

    else:
        return db.get(name)
