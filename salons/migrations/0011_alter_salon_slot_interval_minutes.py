from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('salons', '0010_salon_slot_interval_minutes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salon',
            name='slot_interval_minutes',
            field=models.PositiveSmallIntegerField(
                choices=[(15, '15 minuta'), (30, '30 minuta'), (60, '60 minuta')],
                default=30,
            ),
        ),
    ]
