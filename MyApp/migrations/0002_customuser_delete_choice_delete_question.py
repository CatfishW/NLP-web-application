# Generated by Django 4.1.8 on 2023-06-30 03:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MyApp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username_signup', models.CharField(max_length=150, unique=True)),
                ('email_signup', models.EmailField(max_length=254, unique=True)),
                ('password_signup', models.CharField(max_length=128)),
            ],
        ),
        migrations.DeleteModel(
            name='Choice',
        ),
        migrations.DeleteModel(
            name='Question',
        ),
    ]