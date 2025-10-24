# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchasingitem',
            name='color',
            field=models.CharField(default='#6b7280', help_text='Hex color code for admin display (e.g., #10b981)', max_length=7),
        ),
    ]
