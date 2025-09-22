function OptionChainTable({ rows }) {
  return (
    <div className="option-chain-table">
      <table>
        <thead>
          <tr>
            <th colSpan={5}>CALLS</th>
            <th>Strike</th>
            <th colSpan={5}>PUTS</th>
          </tr>
          <tr>
            <th>OI</th>
            <th>Chg OI</th>
            <th>IV</th>
            <th>Delta</th>
            <th>LTP</th>
            <th></th>
            <th>LTP</th>
            <th>Delta</th>
            <th>IV</th>
            <th>Chg OI</th>
            <th>OI</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.strike} className={row.isAtm ? "atm" : ""}>
              <td>{row.callOi}</td>
              <td>{row.callChgOi}</td>
              <td>{row.callIv}</td>
              <td>{row.callDelta}</td>
              <td>{row.callLtp}</td>
              <td>{row.strike}</td>
              <td>{row.putLtp}</td>
              <td>{row.putDelta}</td>
              <td>{row.putIv}</td>
              <td>{row.putChgOi}</td>
              <td>{row.putOi}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default OptionChainTable;
