function QuickTradeButtons({ onBuy, onSell, onReverse, onSquareOff }) {
  return (
    <div className="quick-trade-controls">
      <button className="btn primary" onClick={onBuy} type="button">
        Buy
      </button>
      <button className="btn danger" onClick={onSell} type="button">
        Sell
      </button>
      <button className="btn secondary" onClick={onReverse} type="button">
        Reverse
      </button>
      <button className="btn outline" onClick={onSquareOff} type="button">
        Square Off
      </button>
    </div>
  );
}

export default QuickTradeButtons;
