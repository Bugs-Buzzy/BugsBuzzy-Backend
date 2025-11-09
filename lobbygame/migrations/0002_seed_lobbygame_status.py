from django.db import migrations


def seed_status_row(apps, schema_editor):
    LobbygameResult = apps.get_model("lobbygame", "LobbygameResult")
    if not LobbygameResult.objects.filter(request_uuid="status").exists():
        LobbygameResult.objects.create(
            request_uuid="status",
            description="not started",
        )


def remove_status_row(apps, schema_editor):
    LobbygameResult = apps.get_model("lobbygame", "LobbygameResult")
    LobbygameResult.objects.filter(request_uuid="status").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("lobbygame", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_status_row, remove_status_row),
    ]
