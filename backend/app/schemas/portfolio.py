from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PositionEntry(BaseModel):
    exchange: str = Field(default="", description="Exchange code such as NSE, BSE")
    tradingsymbol: str = Field(default="", description="Broker tradingsymbol for the instrument")
    symbol_token: str = Field(default="", description="Angel One symbol token", alias="symboltoken")
    product_type: str | None = Field(default=None, description="Product type or margin product", alias="producttype")
    symbol_name: str | None = Field(default=None, description="Readable instrument name", alias="symbolname")
    instrument_type: str | None = Field(default=None, alias="instrumenttype")
    buy_qty: int = Field(default=0, alias="buyqty")
    sell_qty: int = Field(default=0, alias="sellqty")
    buy_amount: float | None = Field(default=None, alias="buyamount")
    sell_amount: float | None = Field(default=None, alias="sellamount")
    buy_avg_price: float | None = Field(default=None, alias="buyavgprice")
    sell_avg_price: float | None = Field(default=None, alias="sellavgprice")
    avg_net_price: float | None = Field(default=None, alias="avgnetprice")
    net_value: float | None = Field(default=None, alias="netvalue")
    net_qty: int = Field(default=0, alias="netqty")
    total_buy_value: float | None = Field(default=None, alias="totalbuyvalue")
    total_sell_value: float | None = Field(default=None, alias="totalsellvalue")
    net_price: float | None = Field(default=None, alias="netprice")
    lot_size: int | None = Field(default=None, alias="lotsize")
    expiry_date: str | None = Field(default=None, alias="expirydate")

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class PositionsResponse(BaseModel):
    net: list[PositionEntry] = Field(default_factory=list, description="Net positions after carry forward")
    day: list[PositionEntry] = Field(default_factory=list, description="Intraday positions for the trading day")


class PositionConvertRequest(BaseModel):
    exchange: str
    symbol_token: str = Field(alias="symboltoken")
    tradingsymbol: str
    old_product_type: str = Field(alias="oldproducttype")
    new_product_type: str = Field(alias="newproducttype")
    transaction_type: str = Field(alias="transactiontype")
    quantity: int
    symbol_name: str | None = Field(default=None, alias="symbolname")
    instrument_type: str | None = Field(default=None, alias="instrumenttype")
    price_den: str | None = Field(default=None, alias="priceden")
    price_num: str | None = Field(default=None, alias="pricenum")
    gen_den: str | None = Field(default=None, alias="genden")
    gen_num: str | None = Field(default=None, alias="gennum")
    precision: str | None = Field(default=None)
    multiplier: str | None = Field(default=None)
    board_lot_size: str | None = Field(default=None, alias="boardlotsize")
    buy_qty: int | None = Field(default=None, alias="buyqty")
    sell_qty: int | None = Field(default=None, alias="sellqty")
    buy_amount: float | None = Field(default=None, alias="buyamount")
    sell_amount: float | None = Field(default=None, alias="sellamount")
    type: str | None = Field(default="DAY")

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class PositionConvertResponse(BaseModel):
    status: bool
    message: str | None = None
    data: Any | None = None


class HoldingEntry(BaseModel):
    tradingsymbol: str
    exchange: str
    isin: str | None = None
    t1_quantity: int = Field(default=0, alias="t1quantity")
    realised_quantity: int = Field(default=0, alias="realisedquantity")
    quantity: int
    authorised_quantity: int = Field(default=0, alias="authorisedquantity")
    product: str | None = None
    collateral_quantity: int | None = Field(default=None, alias="collateralquantity")
    collateral_type: str | None = Field(default=None, alias="collateraltype")
    haircut: float | None = None
    average_price: float | None = Field(default=None, alias="averageprice")
    ltp: float | None = None
    symbol_token: str = Field(alias="symboltoken")
    close: float | None = None
    profit_and_loss: float | None = Field(default=None, alias="profitandloss")
    pnl_percentage: float | None = Field(default=None, alias="pnlpercentage")

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class HoldingSummary(BaseModel):
    total_holding_value: float | None = Field(default=None, alias="totalholdingvalue")
    total_investment_value: float | None = Field(default=None, alias="totalinvvalue")
    total_profit_and_loss: float | None = Field(default=None, alias="totalprofitandloss")
    total_pnl_percentage: float | None = Field(default=None, alias="totalpnlpercentage")

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class HoldingsResponse(BaseModel):
    holdings: list[HoldingEntry] = Field(default_factory=list)
    summary: HoldingSummary | None = Field(default=None, alias="totalholding")

    model_config = ConfigDict(populate_by_name=True)
