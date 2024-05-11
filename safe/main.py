from typing import Optional
import click
from InquirerPy import inquirer
from safe.auth import authenticate_user, create_pswd
from safe.database import Database
from safe.utils import CredentialNameValidator, ItemKeyValidator, print_credentials, print_status, pick_credential


@click.group(chain=True)
@click.version_option()
@click.pass_context
def cli(ctx):
    pswd = authenticate_user()
    db = Database(pswd)
    ctx.obj = db
    ctx.call_on_close(db.close)


@cli.command('add')
@click.pass_obj
def add_command(db: Database):
    """Add a new credential."""
    name = inquirer.text(
        message='Name:',
        instruction='(Ex. Google Account)',
        validate=CredentialNameValidator(db.exists),
        transformer=lambda text: f' {text}'
    ).execute().strip()

    items = {}
    while True:
        key = inquirer.text(
            message='Key:',
            instruction='(Ex. Email)',
            long_instruction='Leave empty to proceed',
            validate=ItemKeyValidator(items),
            transformer=lambda text: f'  {text}' or '  [empty]'
        ).execute().strip()

        if not key:
            break

        value = inquirer.text(
            message='Value:',
            transformer=lambda text: text or '[empty]'
        ).execute().strip()
        items[key] = value

    click.echo('\nPreview and confirmation:\n')
    print_credentials({'name': name, 'items': items}, end='\n')
    choice = inquirer.confirm(
        message='Save it?',
        default=True
    ).execute()
    if choice:
        db.insert(name, items)
        print_status(f'{name} has been saved.\n', 'success')
    else:
        print_status(f'Cancelled\n', 'warning')


@cli.command('get')
@click.option('-n', '--name', help='Name of the credential.')
@click.pass_obj
def get_command(db: Database, name: Optional[str]):
    """Prints a single credential."""
    if db.count == 0:
        click.echo('Database is empty!')
        click.echo('Try adding credential by running:')
        click.secho('  safe add\n', bold=True)
        return

    credential = pick_credential(db, name)
    print_credentials({
        'name': credential.name,
        'items': credential.items_dict
    }, True)


@cli.command('list')
@click.pass_obj
def list_command(db: Database):
    """Prints all the credential."""
    if db.count == 0:
        click.echo('Database is empty!')
        click.echo('Try adding credential by running:')
        click.secho('  safe add\n', bold=True)
        return

    credentials = db.get_all()
    print_credentials([
        {'name': c.name, 'items': c.items_dict}
        for c in credentials
    ], True)


@cli.command('update')
@click.option('-n', '--name', help='Name of the credential.')
@click.pass_obj
def update_command(db: Database, name: Optional[str]):
    """Updates the selected credential."""
    if db.count == 0:
        click.echo('Database is empty!')
        click.echo('Try adding credential by running:')
        click.secho('  safe add\n', bold=True)
        return

    credential = pick_credential(db, name)
    # Used for preview
    previous_name = credential.name

    click.echo('Update previous information:\n')
    new_name = inquirer.text(
        message='New name:',
        instruction=f'(Previous: {credential.name})',
        default=credential.name,
        validate=CredentialNameValidator(db.exists, allow=credential.name),
        transformer=lambda text: f' {text}'
    ).execute().strip()

    new_items = {}
    for key, value in credential.items_dict.items():
        new_key = inquirer.text(
            message='New key:',
            instruction=f'(Previous: {key})',
            long_instruction='Leave empty to delete.',
            default=key,
            validate=ItemKeyValidator(new_items, True),
            transformer=lambda text: f'  {text}' or '  [removed]'
        ).execute().strip()

        if not new_key:
            continue

        new_value = inquirer.text(
            message='New value:',
            instruction=f'(Previous: {value})',
            default=value,
            transformer=lambda text: text or '[empty]'
        ).execute().strip()
        new_items[new_key] = new_value

    click.echo('\nAdd new key-value pairs.\n')
    while True:
        new_key = inquirer.text(
            message='Key:',
            long_instruction='Leave empty to proceed',
            validate=ItemKeyValidator(new_items),
            transformer=lambda text: f'  {text}' or '[empty]'
        ).execute().strip()

        if not new_key:
            break

        new_value = inquirer.text(
            message='Value:',
            transformer=lambda text: text or '[empty]'
        ).execute().strip()
        new_items[new_key] = new_value

    click.echo('\nPreview and confirmation:\n')
    print_credentials({'name': new_name, 'items': new_items}, end='\n')
    choice = inquirer.confirm(
        message='Save the changes?',
        default=True
    ).execute()
    if choice:
        db.update(credential, new_name, new_items)
        print_status(f'{previous_name} has been updated.\n', 'success')
    else:
        print_status(f'Cancelled\n', 'warning')


@cli.command('delete')
@click.option('-n', '--name', help='Name of the credential.')
@click.pass_obj
def delete_command(db: Database, name: Optional[str]):
    """Deletes the selected credential."""
    if db.count == 0:
        click.echo('Database is empty!')
        click.echo('Try adding credential by running:')
        click.secho('  safe add\n', bold=True)
        return

    credential = pick_credential(db, name)

    click.echo('Preview and confirmation:\n')
    print_credentials({
        'name': credential.name,
        'items': credential.items_dict
    }, end='\n')
    choice = inquirer.confirm(message='Delete it?').execute()
    if choice:
        db.delete(credential)
        print_status(f'{credential.name} has been deleted.\n', 'success')
    else:
        print_status(f'Cancelled\n', 'warning')


@cli.command('change-password')
@click.pass_obj
def change_password_command(db: Database):
    """Changes the master password."""
    new_pswd = create_pswd('New password:', True)

    if db.count > 0:
        print_status(
            'Re-encrypting each credential with the new password.\n', start='\n')

    db.change_pswd(new_pswd)
    print_status('Password was safely changed.\n', 'success')
