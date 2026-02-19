from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('salons', '0009_salon_is_active_salon_is_approved'),
    ]

    operations = [
        migrations.AddField(
            model_name='salon',
            name='slot_interval_minutes',
            field=models.PositiveSmallIntegerField(
                choices=[(15, '15 minuta'), (30, '30 minuta')],
                default=30,
            ),
        ),
    ]
