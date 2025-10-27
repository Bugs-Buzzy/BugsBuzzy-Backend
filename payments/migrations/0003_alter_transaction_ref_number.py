# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0002_purchasingitem_color"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="ref_number",
            field=models.BigIntegerField(blank=True, null=True),
        ),
    ]
