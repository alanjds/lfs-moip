#coding: utf-8
import datetime
import logging

from django.db import models
from django.conf import settings

from lfs.plugins import PaymentMethodProcessor
from lfs.plugins import PM_ORDER_ACCEPTED, PM_ORDER_IMMEDIATELY



logger = logging.getLogger("default")


class MoipProcessor(PaymentMethodProcessor):
    """
    Implements MoIP payment processor.
    """

    def process(self):
        if getattr(self, 'order'):
            transaction_id = 'O-%s' % self.order.pk
            price = self.order.price
        elif getattr(self, 'cart'):
            transaction_id = 'C-%s' % self.cart.pk
            price = self.cart.get_price_gross(self.request) # should it be price_net??
        else:
            raise RuntimeError()

        price = '%.0f' % (price*100) # 2 decimal houses, no decimal separator
        bill_title = 'Compra codigo %s em %s' % ( transaction_id, self.request.build_absolute_uri('/').replace('http://', '').strip('/') )

        import ipdb; ipdb.set_trace()
        if getattr(settings, 'MOIP_TOKEN', None):
            # API integration available!
            from moipy.moip import Moip

            moip = Moip(bill_title[:64]) # Docs says "max size = 64 char"

            # Todo: set some person data, to save time
            #address = dict(Logradouro='Rua xxxxx',Numero='222',Bairro='xxxx',Cidade='xxxx',Estado='xx',CEP='xxxxxx',TelefoneFixo='xxxxxxxxxx')
            #self.moip.set_pagador(Nome='xxxx',Email='xxxxxx',Apelido='vitalbh',IdPagador='x',EnderecoCobranca=endereco)

            moip.set_credenciais(token=settings.MOIP_TOKEN, key=settings.MOIP_KEY)
            moip.set_ambiente(getattr(settings, 'MOIP_ENVIRONMENT', 'sandbox'))

            moip.set_valor(price)
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

        elif getattr(settings, 'MOIP_ACCOUNT', None):
            # Only HTML integration available
            from furl import furl
            f = furl('https://www.moip.com.br/PagamentoMoIP.do')
            f.args['id_carteira'] = settings.MOIP_ACCOUNT
            f.args['valor'] = price
            f.args['nome'] = bill_title[:64] # Docs says "max size = 64 char"
            f.args['id_transacao'] = transaction_id
            result = {
                'accepted': True,
                'next_url': f.url,
            }

        else:
            raise RuntimeError('Please configure your MoIP settings.')

        return result

    def get_create_order_time(self):
        return PM_ORDER_ACCEPTED
