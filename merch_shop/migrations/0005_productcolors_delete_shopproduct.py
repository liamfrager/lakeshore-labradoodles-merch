# Generated by Django 4.2.11 on 2024-05-04 23:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('merch_shop', '0004_shopproduct_img'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductColors',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('variant_id', models.IntegerField()),
                ('color_name', models.CharField(max_length=50)),
                ('color_code', models.CharField(max_length=7)),
            ],
        ),
        migrations.DeleteModel(
            name='ShopProduct',
        ),
    ]