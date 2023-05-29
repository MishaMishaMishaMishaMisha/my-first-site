# Generated by Django 4.1.7 on 2023-05-08 09:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0002_remove_choice_votes_no_choice_user_ip'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dashboard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dashboard_name', models.CharField(max_length=200)),
                ('dashboard_key', models.CharField(max_length=200)),
                ('user_ip', models.CharField(max_length=200)),
                ('cr_date', models.DateTimeField(verbose_name='date created')),
            ],
        ),
        migrations.AddField(
            model_name='question',
            name='dashboard',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='polls.dashboard'),
            preserve_default=False,
        ),
    ]
