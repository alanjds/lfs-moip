#coding: utf-8
# python imports
import logging

# django imports
from django.conf import settings

# lfs imports
import lfs.core.signals
from lfs.order.models import Order
from lfs.order.settings import PAID
from lfs.order.settings import PAYMENT_FAILED
from lfs.order.settings import PAYMENT_FLAGGED
from lfs.mail import utils as mail_utils

# lfs-paypal imports
from lfs_moip.models import MoipOrderTransaction

# django-moip imports
from django_moip.html.nit.signals import payment_was_successful, payment_was_flagged
from django_moip.html.redirector.signals import redirector_failed, redirector_successful
from django_moip.html.models import ST_MOIP_COMPLETED

# load logger
logger = logging.getLogger("default")


def mark_payment(moip_obj, order_state=PAID):
    order = None
    try:
        logger.info("MoIP: getting order for uuid %s" % moip_obj.custom)
        order_uuid = moip_obj.custom
        order = Order.objects.get(uuid=order_uuid)
        if order is not None:
            order_old_state = order.state
            order.state = order_state
            order.save()
            if order_old_state != PAID and order_state == PAID:
                lfs.core.signals.order_paid.send({"order": order})
                if getattr(settings, 'LFS_SEND_ORDER_MAIL_ON_PAYMENT', False):
                    mail_utils.send_order_received_mail(order)
    except Order.DoesNotExist, e:
        logger.error("MoIP: %s" % e)
    return order


def successful_payment(sender, **kwargs):
    logger.info("MoIP: successful NIT payment")
    nit_obj = sender
    order = mark_payment(nit_obj, PAID)
    if order is not None:
        transaction, created = MoipOrderTransaction.objects.get_or_create(order=order)
        transaction.nit.add(nit_obj)
        transaction.save()
    else:
        logger.warning("MoIP: successful NIT payment, no order found for uuid %s" % nit_obj.custom)


def unsuccessful_payment(sender, **kwargs):
    logger.info("MoIP: unsuccessful NIT payment")
    nit_obj = sender
    if nit_obj:
        order = None
        if nit_obj.payment_status == ST_MOIP_COMPLETED:
            logger.info("MoIP: payment flaged")
            order = mark_payment(nit_obj, PAYMENT_FLAGGED)
        else:
            logger.info("MoIP: payment failed")
            order = mark_payment(nit_obj, PAYMENT_FAILED)
        if order is not None:
            transaction, created = MoipOrderTransaction.objects.get_or_create(order=order)
            transaction.nit.add(nit_obj)
            transaction.save()
        else:
            logger.warning("MoIP: unsuccessful NIT payment, no order found for uuid %s" % nit_obj.custom)
    else:
        logger.warning("MoIP: unsuccessful NIT payment signal with no NIT object")


def successful_redirector(sender, **kwargs):
    logger.info("MoIP: successful redirector payment")
    redirector_obj = sender
    mark_payment(redirector_obj, True)


def unsuccesful_redirector(sender, **kwargs):
    logger.info("MoIP: unsuccessful redirector payment")
    redirector_obj = sender
    mark_payment(redirector_obj, False)


payment_was_successful.connect(successful_payment, dispatch_uid="Order.nit_successful")
payment_was_flagged.connect(unsuccessful_payment, dispatch_uid="Order.nit_unsuccessful")
redirector_successful.connect(successful_redirector, dispatch_uid="Order.redirector_successful")
redirector_failed.connect(unsuccesful_redirector, dispatch_uid="Order.redirector_unsuccessful")
