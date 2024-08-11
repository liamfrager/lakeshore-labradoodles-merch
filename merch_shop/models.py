from django.db import models


# MODELS
class Color(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=7)


class Product(models.Model):
    id = models.IntegerField(primary_key=True)  # Printful product ID
    name = models.CharField(max_length=100, default='')
    description = models.CharField(max_length=255, default='')
    image = models.URLField(default='')
    preview_images = models.URLField(default='')
    size_prices = models.CharField(max_length=10, default='0')
    colors: list[Color] = None
    sizes = models.CharField(max_length=4, null=True)

    class Meta:
        managed = False


class Variant(models.Model):
    id = models.IntegerField(primary_key=True)  # Printful variant ID
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(decimal_places=2, max_digits=5)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    size = models.CharField(max_length=4)

    class Meta:
        managed = False
