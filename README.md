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
cliente = client.create_sync_client(partner_id='SEU_APP_ID', partner_key='SUA_CHAVE_SECRETA')
result = cliente.get_product_offer(url="https://shopee.com.br/...")
print(result)
# 💽 Se quiser salvar a imagem do produto em memória ou localmente:
cliente.download_product_image(result) 

```

## 🧩 Uso assíncrono básico com `aiohttp`


```python
# Assíncrono
from shopee_affiliate import client
import asyncio
async def main():
    cliente = client.create_async_client(partner_id='SEU_APP_ID', partner_key='SUA_CHAVE_SECRETA')
    result = await cliente.get_product_offer(url="https://shopee.com.br/...")
    print(result)
    # 💽 Se quiser salvar a imagem do produto em memória ou localmente:
    cliente.download_product_image(result)

    # Para obter o link curto de afiliado de algum produto
    link_curto = cliente.get_short_url("https://shopee.com.br/...")
    print(link_curto)
asyncio.run(main())
```

## 🧩 Exibindo a imagem do produto
```bash
pip install pillow shopee-afflib
```
```python

from shopee_affiliate import client
from PIL import Image

# Configurações
PARTNER_ID = 'SEU_APP_ID'
PARTNER_KEY = 'SUA_CHAVE_SECRETA' 

cliente = client.create_sync_client(PARTNER_ID, PARTNER_KEY)
url = "https://shopee.com.br/..."
response = cliente.get_product_offer(url=url)

#baixa a imagem do produto e guarda em  memória pronta para uso
image = cliente.download_product_image(product_data=response, to_memory=True)

# Cria um objeto Image a partir da imagem em memória
new_image = Image.open(image)
# Exibe a imagem
new_image.show()
```


## ⚙️ Recursos principais

- 🔗 Busca de produtos individuais via `shop_id` e `item_id`
- 🔗 Busca de produtos de uma loja via `shop_id`
- 🔗 Busca de produtos aleatórios (sem parametro)
- 🌐 Consulta direta por URL de produto
- 🌐 Obter link curto de afiliado do produto 
- 💾 Download de imagens (em arquivo ou memória)
- 🧠 Versões síncrona e assíncrona

## 🔥 Novidades
v.1.0.5
- Pequenas correções de bugs


## ✨ Créditos
Desenvolvido por **Anthony Santos**
