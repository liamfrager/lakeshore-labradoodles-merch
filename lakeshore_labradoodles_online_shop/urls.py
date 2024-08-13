"""
URL configuration for lakeshore_labradoodles_online_shop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from lakeshore_labradoodles_online_shop import settings
import django.conf.urls.static as static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('merch_shop.urls'))
]
if settings.DEBUG:
    urlpatterns += static.static(settings.STATIC_URL,
                                 document_root=settings.STATIC_ROOT)
