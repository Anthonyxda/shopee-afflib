# shopee_affiliate.py
import time
import hashlib
import json
import requests
import aiohttp
import asyncio
import os
from typing import Optional, Dict, Any, Union, BinaryIO
from io import BytesIO
import re

class ShopeeAffiliateBase:
    """Classe base com funcionalidades comuns"""
    
    def __init__(self, partner_id: str, partner_key: str):
        self.partner_id = partner_id
        self.partner_key = partner_key
        self.base_url = "https://open-api.affiliate.shopee.com.br/graphql"
    
    def _generate_signature(self, timestamp: int, payload: str) -> str:
        """Gera a assinatura SHA256 requerida pela API"""
        base_string = f"{self.partner_id}{timestamp}{payload}{self.partner_key}"
        return hashlib.sha256(base_string.encode('utf-8')).hexdigest()
    
    def _build_headers(self, timestamp: int, payload_str: str) -> Dict[str, str]:
        """Constrói os headers da requisição"""
        signature = self._generate_signature(timestamp, payload_str)
        return {
            "Content-Type": "application/json",
            "Authorization": f"SHA256 Credential={self.partner_id}, Timestamp={timestamp}, Signature={signature}"
        }

class ShopeeAffiliateSync(ShopeeAffiliateBase):
    """Cliente síncrono para a API de Afiliados da Shopee"""
    
    def __init__(self, partner_id: str, partner_key: str):
        super().__init__(partner_id, partner_key)
    
    def graphql_query(self, query: str) -> Dict[str, Any]:
        """
        Executa uma consulta GraphQL de forma síncrona
        
        Args:
            query: String com a query GraphQL
            
        Returns:
            Dict com a resposta da API
        """
        timestamp = int(time.time())
        payload_str = json.dumps({"query": query}, separators=(",", ":"))
        headers = self._build_headers(timestamp, payload_str)
        
        response = requests.post(
            self.base_url,
            headers=headers,
            data=payload_str
        )
        
        response.raise_for_status()
        return response.json()
    
    def get_product_offer(
        self,
        url: str = None,
        by_shop: bool = False,
        shop_id: Union[int, str, None] = None,
        item_id: Union[int, str, None] = None,
        limit: int = 5,
        scroll_id: str | None = None,
        ) -> Dict[str, Any]:
        """
        Busca informações de oferta de produto específico.
        
        Args:
            url: URL do produto Shopee (aceita link curto ou completo).
            by_shop: Pesquise somente produtos da loja a partir da url.
            shop_id: ID da loja (int ou string).
            item_id: ID do produto (int ou string).
            limit: Total de itens por consulta.
            scroll_id: ID da paginação (opcional), saiba mais em https://affiliate.shopee.com.br/open_api/home.
            
        Returns:
            Dict com informações do produto.
        """
        # 🔹 Se uma URL for passada, tenta extrair shop_id e item_id dela
        if url:
            try:
                # Se for link curto, segue redirecionamento
                if "s.shopee.com.br" in url:
                    try:
                        response = requests.get(url, allow_redirects=True, timeout=5)
                        final_url = str(response.url)  # URL final após redirecionamento
                    except requests.RequestException as e:
                        raise RuntimeError(f"Erro ao processar URL Shopee: {e}")
                else:
                    final_url = url

                    # Tenta extrair pelo padrão novo: /product/<shop_id>/<product_id>
                    match = re.search(r'/product/(\d+)/(\d+)', final_url)
                    if match:
                        shop_id, item_id = match.groups()

                    else:
                        # Extrai padrão antigo: -i.<shop_id>.<product_id>
                        match = re.search(r'-i\.(\d+)\.(\d+)', final_url)
                        if match:
                            shop_id, item_id = match.groups()

                    if not (shop_id and item_id):
                        raise ValueError(f"Não foi possível extrair shop_id e item_id da URL: {final_url}")

            except (requests.HTTPError, requests.RequestException) as e:
                raise RuntimeError(f"Erro ao processar URL Shopee: {e}")
            
        # 🔹 Validação de parâmetros
        if item_id and not shop_id:
            raise ValueError("Para consultas de produtos individuais é preciso fornecer o 'shop_id' junto com o 'item_id'.")

        # 🔹 Conversões seguras
        shop_id_str = f"shopId: {int(shop_id)}" if shop_id else ""
        item_id_str = f", itemId: {int(item_id)}" if item_id else ""
        limit_str = f", limit: {limit}" if not item_id else ""  # só aplica 'limit' em listagens
        if by_shop:
            item_id_str = ""
            limit_str = f", limit: {limit}"
        scroll_str = f', scrollId: "{scroll_id}"' if scroll_id else ""

        # 🔹 Campos do GraphQL centralizados (sem repetição)
        fields = """
            productName
            shopName
            shopId
            itemId
            offerLink
            productLink
            price
            commissionRate
            commission
            sales
            imageUrl
            periodStartTime
            periodEndTime
            priceMin
            priceMax
            productCatIds
            ratingStar
            priceDiscountRate
            shopType
            sellerCommissionRate
            shopeeCommissionRate
        """

        # 🔹 Montagem dinâmica do query
        query = f"""
        {{
            productOfferV2({shop_id_str}{item_id_str}{limit_str}{scroll_str}) {{
                nodes {{
                    {fields}
                }}
            }}
        }}
        """
        return self.graphql_query(query)
    
    def get_short_url(self, url: str, sub_ids: list[str] | None = None) -> str:
        """
        Gera um link curto da Shopee via API de Afiliados.

        Args:
            url: URL original do produto Shopee.
            sub_ids: Lista opcional de sub-IDs (ex: ["s1", "s2", "s3"]).

        Returns:
            O link curto (string).
        """
        # 🔹 Garante que a URL é válida
        if not url.startswith("http"):
            raise ValueError("A URL precisa ser completa, incluindo 'http' ou 'https'.")

        # 🔹 Prepara subIds se fornecidos
        sub_ids_str = f'subIds: {json.dumps(sub_ids)}' if sub_ids else ""

        # 🔹 Monta a mutation GraphQL
        query = f"""
        mutation {{
            generateShortLink(input: {{
                originUrl: "{url}",
                {sub_ids_str}
            }}) {{
                shortLink
            }}
        }}
        """

        # 🔹 Executa a query com o método já existente
        response = self.graphql_query(query)

        # 🔹 Trata a resposta
        try:
            return response["data"]["generateShortLink"]["shortLink"]
        except (KeyError, TypeError):
            raise RuntimeError(f"Erro ao gerar link curto: {response}")


    def download_product_image(
        self,
        product_data: dict,
        item_list: int = 0,
        save_path: Optional[str] = None,
        to_memory: bool = False
    ) -> Union[str, BytesIO, None]:
        """
        Baixa a imagem de um produto e salva localmente ou em memória.
        
        Args:
            product_data: Dicionário com dados do produto retornado da API.
            item_list: Índice do item na lista 'nodes' (default: 0).
            save_path: Caminho completo para salvar a imagem (opcional).
            to_memory: Se True, retorna o conteúdo da imagem em BytesIO.
        
        Returns:
            Caminho do arquivo salvo, BytesIO (se to_memory=True), ou None em caso de erro.
        """

        try:
            # 🔹 Extrai dados com segurança
            nodes = product_data.get("data", {}).get("productOfferV2", {}).get("nodes", [])
            if not nodes or item_list >= len(nodes):
                raise ValueError("Índice item_list inválido ou dados do produto incompletos.")

            node = nodes[item_list]
            image_url = node.get("imageUrl")
            item_id = node.get("itemId")

            if not image_url:
                raise ValueError("URL da imagem não encontrada no produto.")

            # 🔹 Faz o download
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()

            # 🔹 Descobre a extensão (padrão: jpg)
            content_type = response.headers.get("Content-Type", "")
            ext = content_type.split("/")[-1].split(";")[0].strip().lower() or "jpg"

            # 🔹 Retorna em memória se solicitado
            if to_memory:
                return BytesIO(response.content)

            # 🔹 Determina o caminho final
            if save_path:
                # Se o caminho for diretório, monta nome do arquivo dentro dele
                if os.path.isdir(save_path):
                    file_path = os.path.join(save_path, f"{item_id}.{ext}")
                else:
                    file_path = save_path
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
            else:
                # Cria arquivo no diretório atual com nome do item
                file_path = f"{item_id}.{ext}"

            # 🔹 Salva o arquivo
            with open(file_path, "wb") as f:
                f.write(response.content)

            print(f"✅ Imagem salva em: {file_path}")
            return file_path

        except requests.RequestException as e:
            print(f"❌ Erro ao baixar a imagem ({type(e).__name__}): {e}")
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")

        return None

class ShopeeAffiliateAsync(ShopeeAffiliateBase):
    """Cliente assíncrono para a API de Afiliados da Shopee"""
    
    def __init__(self, partner_id: str, partner_key: str):
        super().__init__(partner_id, partner_key)
    
    async def graphql_query(self, query: str = None) -> Dict[str, Any]:
        """
        Executa uma consulta GraphQL de forma assíncrona
        
        Args:
            query: String com a query GraphQL
            
        Returns:
            Dict com a resposta da API
        """
        timestamp = int(time.time())
        payload_str = json.dumps({"query": query}, separators=(",", ":")) if query else {}

        headers = self._build_headers(timestamp, payload_str)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                headers=headers,
                data=payload_str
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def get_product_offer(
        self,
        url: str = None,
        by_shop: bool = False,
        shop_id: Union[int, str, None] = None,
        item_id: Union[int, str, None] = None,
        limit: int = 5,
        scroll_id: str | None = None
        ) -> Dict[str, Any]:
        """
        Busca informações de oferta de produto específico.
        
        Args:
            url: URL do produto Shopee (aceita link curto ou completo).
            by_shop: Pesquise somente produtos da loja a partir da url
            shop_id: ID da loja (int ou string).
            item_id: ID do produto (int ou string).
            limit: Total de itens por consulta.
            scroll_id: ID da paginação (opcional), saiba mais em https://affiliate.shopee.com.br/open_api/home.
            pprint: Se for True, retorna a resposta em formato JSON formatado.
            
        Returns:
            Dict com informações do produto.
        """

        # 🔹 Se uma URL for passada, tenta extrair shop_id e item_id dela
        if url:
            try:
                # Verifica se é um link curto (s.shopee.com.br)
                timeout = aiohttp.ClientTimeout(total=5)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, allow_redirects=True) as response:
                        final_url = str(response.url)

                # Extrai padrão novo: /product/<shop_id>/<product_id>
                match = re.search(r'/product/(\d+)/(\d+)', final_url)
                if match:
                    shop_id, item_id = match.groups()

                else:
                    # Extrai padrão antigo: -i.<shop_id>.<product_id>
                    match = re.search(r'-i\.(\d+)\.(\d+)', final_url)
                    if match:
                        shop_id, item_id = match.groups()

                if not (shop_id and item_id):
                    raise ValueError(f"Não foi possível extrair shop_id e item_id da URL: {final_url}")

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                raise RuntimeError(f"Erro ao processar URL Shopee: {e}")

        # 🔹 Validação de parâmetros
        if item_id and not shop_id:
            raise ValueError("Para consultas de produtos individuais é preciso fornecer o 'shop_id' junto com o 'item_id'.")

        # 🔹 Conversões seguras
        shop_id_str = f"shopId: {int(shop_id)}" if shop_id else ""
        item_id_str = f", itemId: {int(item_id)}" if item_id else ""
        limit_str = f", limit: {limit}" if not item_id else ""  # só aplica 'limit' em listagens
        if by_shop:
            item_id_str = ""
            limit_str = f", limit: {limit}"
        scroll_str = f', scrollId: "{scroll_id}"' if scroll_id else ""

        # 🔹 Campos do GraphQL centralizados
        fields = """
            productName
            shopName
            shopId
            itemId
            offerLink
            productLink
            price
            commissionRate
            commission
            sales
            imageUrl
            periodStartTime
            periodEndTime
            priceMin
            priceMax
            productCatIds
            ratingStar
            priceDiscountRate
            shopType
            sellerCommissionRate
            shopeeCommissionRate
        """

        # 🔹 Montagem dinâmica do query
        query = f"""
        {{
            productOfferV2({shop_id_str}{item_id_str}{limit_str}{scroll_str}) {{
                nodes {{
                    {fields}
                }}
            }}
        }}
        """
        # 🔹 Chama a função de consulta GraphQL
        return await self.graphql_query(query)
        
    async def get_short_url(self, url: str, sub_ids: list[str] | None = None) -> str:
        """
        Gera um link curto da Shopee via API de Afiliados.

        Args:
            url: URL original do produto Shopee.
            sub_ids: Lista opcional de sub-IDs (ex: ["s1", "s2", "s3"]).

        Returns:
            O link curto (string).
        """
        # 🔹 Garante que a URL é válida
        if not url.startswith("http"):
            raise ValueError("A URL precisa ser completa, incluindo 'http' ou 'https'.")

        # 🔹 Prepara subIds se fornecidos
        sub_ids_str = f'subIds: {json.dumps(sub_ids)}' if sub_ids else ""

        # 🔹 Monta a mutation GraphQL
        query = f"""
        mutation {{
            generateShortLink(input: {{
                originUrl: "{url}",
                {sub_ids_str}
            }}) {{
                shortLink
            }}
        }}
        """

        # 🔹 Executa a query com o método já existente
        response = self.graphql_query(query)

        # 🔹 Trata a resposta
        try:
            return response["data"]["generateShortLink"]["shortLink"]
        except (KeyError, TypeError):
            raise RuntimeError(f"Erro ao gerar link curto: {response}")
        
    async def download_product_image(
        self,
        product_data: Dict,
        item_list: int = 0,
        save_path: Optional[str] = None,
        to_memory: bool = False,
        timeout: int = 10
    ) -> Optional[Union[str, BytesIO]]:
        """
        Baixa a imagem de um produto da Shopee de forma assíncrona.
        
        Args:
            product_data: Dicionário com os dados do produto
            item_list: Índice do item dentro da lista de produtos
            save_path: Caminho completo para salvar o arquivo (opcional)
            to_memory: Se True, retorna BytesIO em vez de salvar
            timeout: Tempo limite em segundos para o download
        
        Returns:
            - Caminho do arquivo salvo (str)
            - BytesIO se `to_memory=True`
            - None em caso de erro
        """
        try:
            # Extrai URL e ID do produto com segurança
            node = (
                product_data
                .get("data", {})
                .get("productOfferV2", {})
                .get("nodes", [{}])[item_list]
            )
            image_url = node.get("imageUrl")
            item_id = node.get("itemId")

            if not image_url or not item_id:
                print("⚠️ Dados do produto incompletos: imageUrl ou itemId ausente.")
                return None

            # Timeout configurável
            client_timeout = aiohttp.ClientTimeout(total=timeout)

            async with aiohttp.ClientSession(timeout=client_timeout) as session:
                async with session.get(image_url) as response:
                    if response.status != 200:
                        print(f"❌ Erro ao baixar imagem: {response.status}")
                        return None

                    content_type = response.headers.get("Content-Type", "")
                    ext = content_type.split("/")[-1].split(";")[0].strip() or "jpg"

                    # Caso precise retornar em memória
                    if to_memory:
                        image_data = BytesIO(await response.read())
                        return image_data

                    # Define caminho de salvamento
                    if save_path:
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)
                        file_path = save_path
                    else:
                        os.makedirs(str(item_id), exist_ok=True)
                        file_path = os.path.join(str(item_id), f"{item_id}.{ext}")

                    # Salva no disco
                    with open(file_path, "wb") as f:
                        f.write(await response.read())

                    print(f"✅ Imagem salva: {file_path}")
                    return file_path

        except asyncio.TimeoutError:
            print("⏱️ Tempo limite atingido ao baixar a imagem.")
        except aiohttp.ClientError as e:
            print(f"❌ Erro de conexão: {e}")
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")

        return None
        
# Funções de conveniência para criar clientes
def create_sync_client(partner_id: str, partner_key: str) -> ShopeeAffiliateSync:
    """Cria um cliente síncrono"""
    return ShopeeAffiliateSync(partner_id, partner_key)

def create_async_client(partner_id: str, partner_key: str) -> ShopeeAffiliateAsync:
    """Cria um cliente assíncrono"""
    return ShopeeAffiliateAsync(partner_id, partner_key)

