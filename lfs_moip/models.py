# django imports
from django.db import models

# lfs imports
from lfs.order.models import Order

# django-moip imports
from django_moip.html.nit.models import MoipNIT


class MoipOrderTransaction(models.Model):
    order = models.ForeignKey(Order, unique=True)
    ipn = models.ManyToManyField(MoipNIT)


# See https://bitbucket.org/diefenbach/django-lfs/issue/197/
from django_moip.html.nit.views import nit
nit.csrf_exempt = True

from lfs_moip.listeners import *
