import OptionChainTable from "../components/OptionChainTable";
import NotificationBanner from "../components/NotificationBanner";

const mockRows = [
  {
    strike: "24600",
    callOi: "1.28M",
    callChgOi: "+152k",
    callIv: "12.4%",
    callDelta: "0.42",
    callLtp: "212.35",
    putLtp: "188.60",
    putDelta: "-0.39",
    putIv: "13.1%",
    putChgOi: "+98k",
    putOi: "1.02M",
    isAtm: false
  },
  {
    strike: "24650",
    callOi: "1.92M",
    callChgOi: "+302k",
    callIv: "11.8%",
    callDelta: "0.51",
    callLtp: "256.10",
    putLtp: "156.75",
    putDelta: "-0.48",
    putIv: "12.2%",
    putChgOi: "+185k",
    putOi: "1.88M",
    isAtm: true
  },
  {
    strike: "24700",
    callOi: "1.10M",
    callChgOi: "-45k",
    callIv: "11.1%",
    callDelta: "0.34",
    callLtp: "198.45",
    putLtp: "212.20",
    putDelta: "-0.61",
    putIv: "11.7%",
    putChgOi: "+75k",
    putOi: "1.45M",
    isAtm: false
  }
];

function OptionChain() {
  return (
    <section className="page">
      <NotificationBanner
        type="info"
        message="Sample data shown. Live chain wires up once market feed services are ready."
      />
      <h1>Option Chain Analytics</h1>
      <p>Detailed option chain with greeks, OI, and click-to-trade actions.</p>
      <OptionChainTable rows={mockRows} />
    </section>
  );
}

export default OptionChain;
