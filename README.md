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
url = "https://shopee.com.br/..."  # SUA URL DA SHOPEE 
cliente = client.create_sync_client(partner_id='SEU_APP_ID', partner_key='SUA_CHAVE_SECRETA')
result = cliente.get_product_offer(url=url)
print(result)
# 💽 Se quiser salvar a imagem do produto em memória ou localmente:
cliente.download_product_image(result)
# Para obter o link curto de afiliado de algum produto
link_curto = cliente.get_short_url(url)
print(link_curto)
```

## 🧩 Uso assíncrono básico com `aiohttp`


```python
# Assíncrono
from shopee_affiliate import client
import asyncio
async def main():
    url = "https://shopee.com.br/..." # SUA URL DA SHOPEE 
    cliente = client.create_async_client(partner_id='SEU_APP_ID', partner_key='SUA_CHAVE_SECRETA')
    result = await cliente.get_product_offer(url=url)
    print(result)
    # 💽 Se quiser salvar a imagem do produto em memória ou localmente:
    cliente.download_product_image(result)

    # Para obter o link curto de afiliado de algum produto
    link_curto = cliente.get_short_url(url)
    print(link_curto)

asyncio.run(main())
```

## 🧩 Exibindo a imagem do produto com PIL
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

- 🔗 Busca de produtos individuais via `shop_id` e `item_id` ou url
- 🔗 Busca de produtos de uma loja via `shop_id` ou link, e o prametro `by_shop` (defina um limite de itens com `limit`)
- 🔗 Busca de produtos aleatórios (sem parametro)
- 🌐 Consulta direta de produtos de uma loja por URL de produto
- 🌐 Obter link curto de afiliado do produto 
- 💾 Download de imagens (em arquivo ou memória)
- 🧠 Versões síncrona e assíncrona

## 🔥 Novidades

v.1.0.25^
- Adicionados novos campos no json (pós-processamento)
- Pequenos bugs corrigidos.

v.1.0.20
- Várias melhorias no código.
- Nova função adicionada - `get_item_details`
- Função `get_short_url` renomeada para `generate_short_url`

v.1.0.15
- Pequenas correções no código.
- Novo padrão de URL agora é suportado. (Total de 3)
- Corrigido o bug de URL não suportada para alguns links.

v.1.0.10
- Adicionado mais argumentos para busca de seletiva de itens.
- Vaárias melhorias no código.

v.1.0.5
- Adiconado a possibidade de pesquisar produtos de uma loja pela URL.
- Pequenas correções de bugs.

v.1.0.0
- Versão inicial.

## Para ver as categorias dos itens 
👉 https://seller.shopee.com.br/edu/category-guide

## ✨ Créditos
Desenvolvido por **Anthony Santos**
