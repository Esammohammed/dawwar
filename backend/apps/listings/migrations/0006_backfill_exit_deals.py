"""
Data migration for the "صفقة دوّار" architecture revision.

Originally copied data out of apps.exit_deals — ExitListing rows into
Listing.exit_* fields, ExitDocument rows into Media rows with the new
contract/payment_receipt kinds — before that app was uninstalled. See
dawwar-exit-deals-plan.md §2-3 for the full reasoning.

apps.exit_deals no longer exists at all (app + tables both removed once this
migration confirmed the backfill), so this now only guards against ever being
re-run: it always no-ops. It's kept as a real migration file (rather than
deleted) purely as a historical record — deleting an already-applied
migration file breaks `django_migrations` bookkeeping for anyone who already
has it applied.

The reverse migration intentionally does nothing either — if this ever needs
undoing, restore from a DB backup instead.
"""
from django.db import migrations


def backfill_forward(apps, schema_editor):
    # No-op: apps.exit_deals (and its ExitListing/ExitDocument tables) is
    # gone. This function only still exists because the migration already
    # ran once, for real, while that app was present — see the module
    # docstring. Do not resurrect the exit_deals lookup here.
    return


def backfill_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0005_listing_developer_current_price_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_forward, backfill_reverse),
    ]
