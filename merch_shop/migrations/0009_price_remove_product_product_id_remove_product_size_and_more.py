# Generated by Django 4.2.11 on 2024-05-13 18:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('merch_shop', '0008_color_product_variant_delete_productvariant'),
    ]

    operations = [
        migrations.CreateModel(
            name='Price',
            fields=[
                ('id', models.CharField(max_length=30, primary_key=True, serialize=False)),
                ('value', models.DecimalField(decimal_places=2, max_digits=5)),
            ],
        ),
        migrations.RemoveField(
            model_name='product',
            name='product_id',
        ),
        migrations.RemoveField(
            model_name='product',
            name='size',
        ),
        migrations.RemoveField(
            model_name='variant',
            name='stripe_price_id',
        ),
        migrations.RemoveField(
            model_name='variant',
            name='variant_id',
        ),
        migrations.AddField(
            model_name='product',
            name='sizes',
            field=models.CharField(choices=[('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL'), ('2XL', '2XL'), ('3XL', '3XL'), ('4XL', '4XL'), ('5XL', '5XL')], default=None, max_length=4),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='product',
            name='id',
            field=models.IntegerField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='variant',
            name='id',
            field=models.IntegerField(primary_key=True, serialize=False),
        ),
        migrations.AddField(
            model_name='variant',
            name='price',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='merch_shop.price'),
            preserve_default=False,
        ),
    ]