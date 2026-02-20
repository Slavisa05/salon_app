from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('salons', '0011_alter_salon_slot_interval_minutes'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='cancellation_reason',
            field=models.TextField(blank=True),
        ),
    ]
