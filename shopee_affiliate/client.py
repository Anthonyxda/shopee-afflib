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
        Executa uma consulta GraphQL de forma síncrona.
        
        Args:
            query: String com a query GraphQL
            
        Returns:
            Dict com a resposta da API
        """
        timestamp = int(time.time())
        payload = {"query": query}
        payload_str = json.dumps(payload, separators=(",", ":"))
        headers = self._build_headers(timestamp, payload_str)
        
        response = requests.post(
            self.base_url,
            headers=headers,
            data=payload_str,
            timeout=30  # Adicionar timeout é uma boa prática
        )
        response.raise_for_status()
        return response.json()

    def _extract_ids_from_url(self, url: str) -> tuple[str, str]:
        """Extrai shop_id e item_id de URLs da Shopee."""
        try:
            if "s.shopee.com.br" in url:  # Link curto
                response = requests.get(url, allow_redirects=True, timeout=10)
                final_url = response.url
            else:
                final_url = url

            # Padrão novo: /product/<shop_id>/<product_id>
            match = re.search(r'/product/(\d+)/(\d+)', str(final_url))
            if match:
                return match.groups()

            # Padrão antigo: -i.<shop_id>.<product_id>
            match = re.search(r'-i\.(\d+)\.(\d+)', str(final_url))
            if match:
                return match.groups()

            raise ValueError(f"Formato de URL não suportado: {url}")

        except requests.RequestException as e:
            raise RuntimeError(f"Erro ao processar URL: {e}")

    def get_product_offer(
        self,
        url: str = None,
        byShop: bool = False,
        shopId: Union[int, str, None] = None,
        itemId: Union[int, str, None] = None,
        keyword: str | None = None,
        shopType: str | None = None,
        page: int | None = None,
        limit: int = 5,
        sortType: str | None = None,
        productCatId: int | None = None,
        isAMSOffer: bool | None = None,
        isKeySeller: bool | None = None,
        scrollId: str | None = None
    ) -> Dict[str, Any]:
        """
        Busca informações de oferta de produto específico.
        
        Args:
            url: URL do produto Shopee (aceita link curto ou completo)
            by_shop: Filtrar apenas por loja
            shopId: ID da loja
            itemId: ID do produto
            keyword: Termo de busca
            shopType: Tipo de loja
            page: Número da página
            limit: Itens por página (default: 5)
            sortType: Tipo de ordenação (1, 2, 3)
            productCatId: ID da categoria
            isAMSOffer: Filtro para ofertas AMS
            isKeySeller: Filtro para vendedores chave
            scrollId: ID para paginação

        Returns:
            Dict com informações do produto

        Raises:
            ValueError: Quando há parâmetros inválidos ou ausentes
            RuntimeError: Erro ao processar URL
        """
        # Validações iniciais
        if sortType and sortType not in (1, 2, 3):
            raise ValueError("sortType deve ser 1, 2 ou 3")

        # Extração de IDs da URL se fornecida
        if url:
            shop_id, item_id = self._extract_ids_from_url(url)

        if url and (shopId or itemId):
            raise ValueError("Não é possível passar uma url com shopId ou itemId)")
            
        # Validação de parâmetros obrigatórios
        if item_id and not shop_id:
            raise ValueError("shop_id é obrigatório para consultas com item_id")
        
        if byShop and not shop_id:
            raise ValueError("shop_id é obrigatório quando by_shop=True")

        # Construção dos argumentos da query
        args = []

        if shop_id:
            args.append(f"shopId: {int(shop_id)}")
        
        # Lógica para item_id vs listagem
        if item_id and not byShop:
            # Consulta de produto específico
            args.append(f"itemId: {int(item_id)}")
        else:
            # Listagem (por loja ou geral) - permite paginação e limite
            if limit:
                args.append(f"limit: {limit}")
            if page:
                args.append(f"page: {page}")
            if scrollId:
                args.append(f'scrollId: "{scrollId}"')

        # Parâmetros de busca/filtro (apenas para listagens)
        if keyword and not byShop:  # Não permite keyword com by_shop
            args.append(f"keyword: '{keyword}'")
        
        if productCatId:
            args.append(f"productCatId: {productCatId}")
        
        if isAMSOffer is not None:
            args.append(f"isAMSOffer: {str(isAMSOffer).lower()}")
        
        if isKeySeller is not None:
            args.append(f"isKeySeller: {str(isKeySeller).lower()}")
        
        if shopType:
            args.append(f"shopType: {shopType}")
        
        if sortType:
            args.append(f"sortType: {sortType}")

        # Campos fixos da resposta
        fields = """
            productName
            shopName
            shopId
            itemId
            productCatIds
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
            ratingStar
            priceDiscountRate
            shopType
            sellerCommissionRate
            shopeeCommissionRate
        """

        # Montagem final da query
        query_args = ", ".join(args)
        query = f"""
        {{
            productOfferV2({query_args}) {{
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
    
    async def graphql_query_async(self, query: str) -> Dict[str, Any]:
        """
        Executa uma consulta GraphQL de forma assíncrona.
        
        Args:
            query: String com a query GraphQL
            
        Returns:
            Dict com a resposta da API
        """
        timestamp = int(time.time())
        payload = {"query": query}
        payload_str = json.dumps(payload, separators=(",", ":"))
        headers = self._build_headers(timestamp, payload_str)
        
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                self.base_url,
                headers=headers,
                data=payload_str
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def _extract_ids_from_url_async(self, url: str) -> tuple[str, str]:
        """Extrai shop_id e item_id de URLs da Shopee de forma assíncrona."""
        try:
            if "s.shopee.com.br" in url:  # Link curto
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, allow_redirects=True) as response:
                        final_url = str(response.url)  # URL final após redirecionamento
            else:
                final_url = url

            # Padrão novo: /product/<shop_id>/<product_id>
            match = re.search(r'/product/(\d+)/(\d+)', final_url)
            if match:
                return match.groups()

            # Padrão antigo: -i.<shop_id>.<product_id>
            match = re.search(r'-i\.(\d+)\.(\d+)', final_url)
            if match:
                return match.groups()

            raise ValueError(f"Formato de URL não suportado: {url}")

        except aiohttp.ClientError as e:
            raise RuntimeError(f"Erro ao processar URL: {e}")

    async def get_product_offer_async(
        self,
        url: str = None,
        byShop: bool = False,
        shopId: Union[int, str, None] = None,
        itemId: Union[int, str, None] = None,
        keyword: str | None = None,
        shopType: str | None = None,
        page: int | None = None,
        limit: int = 5,
        sortType: str | None = None,
        productCatId: int | None = None,
        isAMSOffer: bool | None = None,
        isKeySeller: bool | None = None,
        scrollId: str | None = None
    ) -> Dict[str, Any]:
        """
        Busca informações de oferta de produto específico de forma assíncrona.
        
        Args:
            url: URL do produto Shopee (aceita link curto ou completo)
            byShop: Filtrar apenas por loja
            shopId: ID da loja
            itemId: ID do produto
            keyword: Termo de busca
            shopType: Tipo de loja
            page: Número da página
            limit: Itens por página (default: 5)
            sortType: Tipo de ordenação (1, 2, 3)
            productCatId: ID da categoria
            isAMSOffer: Filtro para ofertas AMS
            isKeySeller: Filtro para vendedores chave
            scrollId: ID para paginação

        Returns:
            Dict com informações do produto

        Raises:
            ValueError: Quando há parâmetros inválidos ou ausentes
            RuntimeError: Erro ao processar URL
        """
        # Validações iniciais
        if sortType and sortType not in (1, 2, 3):
            raise ValueError("sortType deve ser 1, 2 ou 3")

        # Inicializa variáveis
        shop_id = shopId
        item_id = itemId

        # Extração de IDs da URL se fornecida
        if url:
            shop_id, item_id = await self._extract_ids_from_url_async(url)

        if url and (shopId or itemId):
            raise ValueError("Não é possível passar uma url com shopId ou itemId")
                
        # Validação de parâmetros obrigatórios
        if item_id and not shop_id:
            raise ValueError("shop_id é obrigatório para consultas com item_id")
        
        if byShop and not shop_id:
            raise ValueError("shop_id é obrigatório quando byShop=True")

        # Construção dos argumentos da query
        args = []

        if shop_id:
            args.append(f"shopId: {int(shop_id)}")
        
        # Lógica para item_id vs listagem
        if item_id and not byShop:
            # Consulta de produto específico
            args.append(f"itemId: {int(item_id)}")
        else:
            # Listagem (por loja ou geral) - permite paginação e limite
            if limit:
                args.append(f"limit: {limit}")
            if page:
                args.append(f"page: {page}")
            if scrollId:
                args.append(f'scrollId: "{scrollId}"')

        # Parâmetros de busca/filtro (apenas para listagens)
        if keyword and not byShop:  # Não permite keyword com byShop
            args.append(f"keyword: '{keyword}'")
        
        if productCatId:
            args.append(f"productCatId: {productCatId}")
        
        if isAMSOffer is not None:
            args.append(f"isAMSOffer: {str(isAMSOffer).lower()}")
        
        if isKeySeller is not None:
            args.append(f"isKeySeller: {str(isKeySeller).lower()}")
        
        if shopType:
            args.append(f"shopType: {shopType}")
        
        if sortType:
            args.append(f"sortType: {sortType}")

        # Campos fixos da resposta
        fields = """
            productName
            shopName
            shopId
            itemId
            productCatIds
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
            ratingStar
            priceDiscountRate
            shopType
            sellerCommissionRate
            shopeeCommissionRate
        """

        # Montagem final da query
        query_args = ", ".join(args)
        query = f"""
        {{
            productOfferV2({query_args}) {{
                nodes {{
                    {fields}
                }}
            }}
        }}
        """

        return await self.graphql_query_async(query)
        
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

