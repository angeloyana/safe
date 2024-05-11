from typing import Optional
import os
import sys
import bcrypt
import click
from InquirerPy import inquirer
from InquirerPy.validator import EmptyInputValidator
from safe.config import config
from safe.utils import print_status


def create_pswd(
    pswd_prompt: Optional[str] = 'Create password:',
    concise: Optional[bool] = False
) -> str:
    """Prompt that create and saves master password.

    Args:
        concise: To not show title or status message.

    Returns:
        Master password used for encryption.
    """
    if not concise:
        click.echo(
            f"Create your {click.style('master password', bold=True)} to get started.")
        click.echo('Press Ctrl-C to cancel.\n')

    pswd = inquirer.secret(
        message=pswd_prompt,
        validate=EmptyInputValidator('The prompt is empty'),
        transformer=lambda _: '[hidden]'
    ).execute().strip()

    # For password confirmation only
    inquirer.secret(
        message='Confirm password:',
        instruction='(Re-enter the password)',
        validate=lambda text: text == pswd,
        invalid_message='Password did not match.',
        transformer=lambda _: '[hidden]'
    ).execute()

    with open(config['path']['password'], 'wb') as f:
        hashed_pswd = bcrypt.hashpw(pswd.encode(), bcrypt.gensalt())
        f.write(hashed_pswd)
        if not concise:
            print_status('Password has been saved.\n', 'success')
        return pswd


def verify_user() -> str:
    click.echo(
        f"Enter your {click.style('master password', bold=True)} to proceed.")
    click.echo('Press Ctrl-C to cancel.\n')

    pswd = inquirer.secret(
        message='Password:',
        transformer=lambda _: '[hidden]'
    ).execute().strip()

    with open(config['path']['password'], 'rb') as f:
        hashed_pswd = f.read()
        if bcrypt.checkpw(pswd.encode(), hashed_pswd):
            print_status('Password has been verified.\n', 'success')
            return pswd
        print_status('Incorrect password\n', 'error')
        sys.exit(1)


def authenticate_user() -> str:
    """Prompts user for the master password if it was already created.
    Otherwise, creates one.

    Returns:
        Master password used for encryption.
    """
    if not os.path.isfile(config['path']['password']):
        return create_pswd()
    return verify_user()
