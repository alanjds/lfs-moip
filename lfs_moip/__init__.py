# python imports
import locale

# lfs imports
from lfs.plugins import PaymentMethodProcessor
from lfs.plugins import PM_ORDER_IMMEDIATELY
from lfs.caching.utils import lfs_get_object_or_404
from lfs.core.models import Shop

# django imports
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse

# django django_moip imports
from django_moip.html.conf import POSTBACK_ENDPOINT
from django_moip.html.conf import SANDBOX_POSTBACK_ENDPOINT
from django_moip.html.forms import MoipPaymentsForm


class MoipProcessor(PaymentMethodProcessor):
    def process(self):
        import ipdb; ipdb.set_trace()
        if getattr(settings, 'LFS_MOIP_INTEGRATION', 'HTML').upper() == 'API':
            return {
                "accepted": True,
                "next_url": reverse("lfs_thank_you"),
            }
        else:
            return {
                "accepted": True,
                "next_url": self.order.get_pay_link(self.request),
            }

    def get_create_order_time(self):
        return PM_ORDER_IMMEDIATELY

    def get_pay_link(self):
        shop = lfs_get_object_or_404(Shop, pk=1)
        current_site = Site.objects.get(id=settings.SITE_ID)

        #notify_url = "http://" + current_site.domain + reverse('moip-nit')
        redirector_url = "http://" + current_site.domain + reverse('lfs_thank_you')

        import ipdb; ipdb.set_trace()
        info = {
            "id_carteira": settings.MOIP_RECEIVER_EMAIL,
            "id_transacao": self.order.uuid,
            "pagador_nome": (u'%s %s' %(self.order.invoice_firstname, self.order.invoice_lastname)).strip(),
            "pagador_logradouro": self.order.invoice_line1,
            "pagador_complemento": self.order.invoice_line2,
            "pagador_cidade": self.order.invoice_city,
            "pagador_estado": self.order.invoice_state,
            "pagador_cep": self.order.invoice_code,
            #"frete": "1",
            "nome": u"%s - %s" % (shop.name, shop.shop_owner),
            "valor": "%i" % ((self.order.price - self.order.tax)*100), # no decimal dot
        }
        form = MoipPaymentsForm(data=info)
        link = form.get_link()

        #if getattr(settings, 'MOIP_DEBUG', settings.DEBUG):
        #    url = SANDBOX_POSTBACK_ENDPOINT + "?" + parameters
        #else:
        #    url = POSTBACK_ENDPOINT + "?" + parameters

        return link
