import urllib, logging
from cgi import parse_qs

from django.conf import settings
from satchmo.utils.dynamic import lookup_url

log = logging.getLogger()

class PayPal:
    """ #PayPal utility class"""
    signature_values = {}
    API_ENDPOINT = ""
    PAYPAL_URL = ""
    return_url = ""
    cancel_url = ""
    shop_logo = ""
    localecode = ""
    
    def __init__(self, payment_module):
        if payment_module.LIVE.value:
            log.debug("live order on %s", payment_module.KEY.value)
            self.PAYPAL_URL = payment_module.POST_URL.value
            self.API_ENDPOINT = payment_module.ENDPOINT_URL.value
            
            #account = payment_module.BUSINESS.value
        else:
            log.debug("test order on %s", payment_module.KEY.value)
            self.PAYPAL_URL = payment_module.POST_TEST_URL.value
            self.API_ENDPOINT = payment_module.ENDPOINT_TEST_URL.value

        ## Sandbox values
        self.signature_values = {
        'USER' : payment_module.API_USER.value, 
        'VENDOR' : payment_module.API_MERCHANT_LOGIN_ID.value,
        'PARTNER' : payment_module.API_PARTNER.value,
        'PWD' : payment_module.API_PASSWORD.value
        }

        self.signature = urllib.urlencode(self.signature_values) + "&"
        
        
        self.return_url = lookup_url(payment_module, 'satchmo_checkout-step2')
        self.return_url = "http://" + settings.SITE_DOMAIN + self.return_url
        
        self.cancel_url = lookup_url(payment_module, 'satchmo_checkout-cancel')
        self.cancel_url = "http://" + settings.SITE_DOMAIN + self.cancel_url
        
        if payment_module.SHOP_LOGO.value.startswith("http"):
            self.shop_logo = payment_module.SHOP_LOGO.value
        else:	
            self.shop_logo = "http://" + settings.SITE_DOMAIN + payment_module.SHOP_LOGO.value
            self.localecode = payment_module.DEFAULT_LOCALECODE.value.upper().encode() # from unicode

    # API METHODS
    def SetExpressCheckout(self, params):
        default_params = {
            'ACTION' : "S", # SetExpressCheckout
            'NOSHIPPING' : 1,
            'TRXTYPE' : 'S', # Sale
            'RETURNURL' : self.return_url,
            'CANCELURL' : self.cancel_url,
            'TENDER': 'P', # Paypal
            'AMT' : 100,
        }
        default_params.update(params)
        params_string = self.signature + urllib.urlencode(default_params)
        
        #weired API quirk
        params_string = params_string.replace(r"%3A", ":").replace(r"%2F", "/")
        
        response = urllib.urlopen(self.API_ENDPOINT, params_string).read()
        response_dict = parse_qs(response)
        try:
            response_token = response_dict['TOKEN'][0]
            return response_token
            
        except:
            log.info("Unvalid Paypal API settings")
            assert False
        
    
    def GetExpressCheckoutDetails(self, token, return_all = False):
        default_params = {
            'ACTION' : "G", # GetExpressCheckoutDetails
            'TRXTYPE': 'S', # Sale
            'TENDER' : 'P',
            'RETURNURL' : self.return_url, 
            'CANCELURL' : self.cancel_url,  
            'TOKEN' : token,
        }
        #default_params.update(params)
        params_string = self.signature + urllib.urlencode(default_params)
        
        #weired API quirk
        params_string = params_string.replace(r"%3A", ":").replace(r"%2F", "/")
        
        response = urllib.urlopen(self.API_ENDPOINT, params_string).read()
        response_dict = parse_qs(response)
        if return_all:
            return response_dict
        try:
            response_token = response_dict['TOKEN'][0]
        except KeyError:
            response_token = response_dict
        return response_token
    
    def DoExpressCheckoutPayment(self, params):
        
        default_params = {
            'ACTION' : "D", # DoExpressCheckoutPayment
            'TRXTYPE' : 'S', # Sale
            'RETURNURL' : self.return_url,#'http://www.yoursite.com/returnurl', #edit this 
            'CANCELURL' : self.cancel_url,#'http://www.yoursite.com/cancelurl', #edit this 
            'TENDER' : 'P', # Paypal
            #'TOKEN' : token,
            #'AMT' : amt,
            #'PAYERID' : payer_id,
        }
        
        default_params.update(params)
                     
        params_string = self.signature + urllib.urlencode(default_params)
        
        #weired API quirk
        params_string = params_string.replace(r"%3A", ":").replace(r"%2F", "/")
        
        response = urllib.urlopen(self.API_ENDPOINT, params_string).read()
        response_tokens = {}
        for token in response.split('&'):
            response_tokens[token.split("=")[0]] = token.split("=")[1]
        for key in response_tokens.keys():
                response_tokens[key] = urllib.unquote(response_tokens[key])
        return response_tokens
        
    def GetTransactionDetails(self, tx_id):
        params = {
            'ACTION' : "G", # GetTransactionDetails 
            'TRXTYPE' : 'S',
            'TENDER' : 'P',
            'TRANSACTIONID' : tx_id,
        }
        params_string = self.signature + urllib.urlencode(params)
        
        #weired API quirk
        params_string = params_string.replace(r"%3A", ":").replace(r"%2F", "/")
        
        response = urllib.urlopen(self.API_ENDPOINT, params_string).read()
        response_tokens = {}
        for token in response.split('&'):
            response_tokens[token.split("=")[0]] = token.split("=")[1]
        for key in response_tokens.keys():
                response_tokens[key] = urllib.unquote(response_tokens[key])
        return response_tokens
