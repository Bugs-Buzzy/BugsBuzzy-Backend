# Generated manually on 2025-11-09
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lobbygame", "0002_lobbygamestatus_alter_lobbygameresult_request_uuid"),
    ]

    operations = [
        migrations.AddField(
            model_name="lobbygameresult",
            name="discount_percentage",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="lobbygameresult",
            name="coupon_code",
            field=models.CharField(blank=True, max_length=32, null=True, unique=True),
        ),
    ]
