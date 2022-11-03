import click

from .featurestore_sync import feature_store_sync


@click.group()
def cli():
    """Click group for feature store commands."""
    click.echo("⭐ Domino FeatureStore CLI tool ⭐")


@cli.command()
@click.option(
    "--skip-source-validation",
    is_flag=True,
    help="Don't validate the data sources by checking for that the tables exist.",
)
def sync(skip_source_validation: bool) -> None:
    """Synchronize feast registry and domino feature views with feast source code"""
    feature_store_sync(skip_source_validation)
