# 🛒 Shopee AffLib

Biblioteca Python para integração com a **API de Afiliados da Shopee** —
suporta chamadas **síncronas e assíncronas**, geração de links, e download de imagens.

## 🚀 Instalação

```bash
pip install shopee-afflib
```

## 🧩 Uso sincrono básico

```python
# Sincrono
from shopee_affiliate import client
cliente = client.create_sync_client(partner_id="YOUR_PARTNER_ID", partner_key="YOUR_PARTNER_KEY")
result = cliente.get_product_offer(url="https://shopee.com.br/...")
print(result)
# 💽 Se quiser salvar a imagem do produto em memória ou localmente:
cliente.download_product_image(result)
# Para obter o link curto de afiliado de algum produto
link_curto = cliente.get_short_url("https://shopee.com.br/...")
print(link_curto)
```

## 🧩 Uso assincrono básico

```python
# Sincrono
from shopee_affiliate import client
import asyncio
async def main():
    cliente = client.create_async_client(partner_id="YOUR_PARTNER_ID", partner_key="YOUR_PARTNER_KEY")
    result = await cliente.get_product_offer(url="https://shopee.com.br/...")
    print(result)
    # 💽 Se quiser salvar a imagem do produto em memória ou localmente:
    cliente.download_product_image(result)

    # Para obter o link curto de afiliado de algum produto
    link_curto = cliente.get_short_url("https://shopee.com.br/...")
    print(link_curto)
asyncio.run(main())
```

## ⚙️ Recursos principais

- 🔗 Busca de produtos individuais via `shop_id` e `item_id`
- 🔗 Busca de produtos de uma loja via `shop_id`
- 🔗 Busca de produtos aleatórios (sem parametro)
- 🌐 Consulta direta por URL de produto
- 🌐 Obter link curto de afiliado do produto 
- 💾 Download de imagens (em arquivo ou memória)
- 🧠 Versões síncrona e assíncrona

## ✨ Créditos
Desenvolvido por **Anthony Santos**
