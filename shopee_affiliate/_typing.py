from typing import Literal

# campos fixos da resposta da função get_product_offer
ofert_fields = """
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
# Campos fixos da resposta da função get_item_details
details_fields = Literal[
    "productName",
    "shopName",
    "shopId",
    "itemId",
    "productCatIds",
    "offerLink",
    "productLink",
    "price",
    "originalPrice",
    "commissionRate",
    "commission",
    "sales",
    "imageUrl",
    "periodStartTime",
    "periodEndTime",
    "priceMin",
    "originalPriceMin",
    "priceMax",
    "originalPriceMax",
    "ratingStar",
    "priceDiscountRate",
    "shopType",
    "sellerCommissionRate",
    "shopeeCommissionRate"
]
