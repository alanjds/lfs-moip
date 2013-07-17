#coding: utf-8
import datetime
import logging

from django.db import models
from django.conf import settings

from lfs.plugins import PaymentMethodProcessor


logger = logging.getLogger("default")


class MoipProcessor(PaymentMethodProcessor):
    def process(self):
        if getattr(self, 'order'):
            transaction_id = 'ORD#%s' % self.order.pk
        elif getattr(self, 'cart'):
            transaction_id = 'CAR#%s' % self.cart.pk
        else:
            raise RuntimeError()

        bill_text = 'Compra %s em %s' % ( transaction_id, self.request.build_absolute_uri('/').replace('http://', '').strip('/') )

        if 'MOIP_TOKEN' in settings:
            # API integration available!
            from moipy.moip import Moip

            moip = Moip(bill_text[:64]) # Docs says "max size = 64 char"

            # Todo: set some person data, to save time
            #address = dict(Logradouro='Rua xxxxx',Numero='222',Bairro='xxxx',Cidade='xxxx',Estado='xx',CEP='xxxxxx',TelefoneFixo='xxxxxxxxxx')
            #self.moip.set_pagador(Nome='xxxx',Email='xxxxxx',Apelido='vitalbh',IdPagador='x',EnderecoCobranca=endereco)

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

        elif 'MOIP_ACCOUNT' in settings:
            # Only HTML integration available
            import furl

        else:
            raise RuntimeError('Please configure your MoIP settings.')

        return result


    def get_create_order_time(self):
        return PM_ORDER_ACCEPTED
