from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sistem_zakazivanja', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='email_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='pending_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
    ]
