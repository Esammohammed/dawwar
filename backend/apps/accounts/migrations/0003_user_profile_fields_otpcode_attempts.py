from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_otpcode_delivery_method_otpcode_email_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='address',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='user',
            name='governorate',
            field=models.CharField(blank=True, choices=[('cairo', 'Cairo'), ('giza', 'Giza'), ('alexandria', 'Alexandria'), ('qalyubia', 'Qalyubia'), ('sharqia', 'Sharqia'), ('dakahlia', 'Dakahlia'), ('beheira', 'Beheira'), ('gharbia', 'Gharbia'), ('monufia', 'Monufia'), ('kafr_el_sheikh', 'Kafr El Sheikh'), ('damietta', 'Damietta'), ('port_said', 'Port Said'), ('ismailia', 'Ismailia'), ('suez', 'Suez'), ('north_sinai', 'North Sinai'), ('south_sinai', 'South Sinai'), ('red_sea', 'Red Sea'), ('matrouh', 'Matrouh'), ('new_valley', 'New Valley'), ('fayoum', 'Fayoum'), ('beni_suef', 'Beni Suef'), ('minya', 'Minya'), ('assiut', 'Assiut'), ('sohag', 'Sohag'), ('qena', 'Qena'), ('luxor', 'Luxor'), ('aswan', 'Aswan')], default='', max_length=32),
        ),
        migrations.AddField(
            model_name='user',
            name='city',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='user',
            name='date_of_birth',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='national_id',
            field=models.CharField(blank=True, default='', max_length=14),
        ),
        migrations.AddField(
            model_name='otpcode',
            name='attempts',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='otpcode',
            name='purpose',
            field=models.CharField(choices=[('register', 'Register'), ('login', 'Login'), ('reset', 'Password Reset')], default='login', max_length=20),
        ),
    ]
