"""
Shopee Affiliate Library
------------------------
Biblioteca para integrar com a API de Afiliados da Shopee.

Usage::
    >>> # Modo sincrono
    >>> from shopee_affiliate import client
    >>> cliente = client.create_sync_client(partner_id="123", partner_key="abc")
    >>> result = cliente.get_product_offer(url="https://shopee.com.br/...")
    >>> print(result)

    >>> # Modo assíncrono
    >>> from shopee_affiliate import client
    >>> import asyncio

    >>> async def main():
    >>>     cliente = client.create_async_client(partner_id="123", partner_key="abc")
    >>>     result = await cliente.get_product_offer(url="https://shopee.com.br/...")
    >>>     print(result)

Detalhes

#Repositório: https://github.com/seuusuario/shopee-affiliate
"""

from .client import (
    ShopeeAffiliateBase,
    ShopeeAffiliateSync,
    ShopeeAffiliateAsync,
    create_sync_client,
    create_async_client
)


__version__ = "1.0.0"
__author__ = "Anthony Santos"
