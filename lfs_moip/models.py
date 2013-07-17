#coding: utf-8
import datetime
import logging

from django.db import models
from django.conf import settings

from lfs.plugins import PaymentMethodProcessor

from moipy.moip import Moip


logger = logging.getLogger("default")


class MoipProcessor(PaymentMethodProcessor):
    def process(self):
        if getattr(self, 'order'):
            transaction_id = 'ORD#%s' % self.order.pk
        elif getattr(self, 'cart'):
            transaction_id = 'CAR#%s' % self.cart.pk
        else:
            raise RuntimeError()

        moip = Moip('Pedido %s em %s' % ( transaction_id, self.request.build_absolute_uri('/').replace('http://', '').strip('/') ))

        moip.set_credenciais(token=settings.MOIP_TOKEN, key=settings.MOIP_KEY)
        moip.set_ambiente(settings.get('MOIP_ENVIRONMENT', 'sandbox'))
        moip.set_valor(self.order.price)
        moip.set_data_vencimento(datetime.date.today().strftime('%Y-%m-%d')) # yyyy-mm-dd

        moip.set_id_proprio(transaction_id)
        moip.envia()

        answer = moip.get_resposta() # {sucesso:'Sucesso','token':'KJHSDASKD392847293AHFJKDSAH'}
        logger.info('MoIP Answer: %s' % answer)
        if answer.get('sucesso', '').lower() == 'sucesso':
            accepted = True
        else:
            accepted = False

        result = {
            'accepted': accepted,
        }

        if accepted:
            result['next_url'] = u'http://moip.com.br/payment?token=%s' % token

        return result


    def get_create_order_time(self):
        return PM_ORDER_ACCEPTED
