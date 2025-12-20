import { ChangeEvent, useRef } from "react";

const Ticket = ({
  tickets,
  rowIndex,
  colIndex,
  changeTickets,
  selectedColor,
}: {
  tickets: {
    tempBackground: string;
    color: string;
    bold: boolean;
    colspan: number;
    value: string;
    circuitNumber: { color: string; bold: boolean; value: string };
  }[][];
  rowIndex: number;
  colIndex: number;
  changeTickets: (
    newTickets: {
      tempBackground: string;
      color: string;
      bold: boolean;
      colspan: number;
      value: string;
      circuitNumber: { color: string; bold: boolean; value: string };
    }[][],
  ) => void;
  selectedColor: string;
}) => {
  const ticketInfo = tickets[rowIndex][colIndex];
  // set the different element classes depending on the state color values
  const circuitClasses = `circuit ${ticketInfo.tempBackground}Back`;
  const circuitNumberClasses = `circuitNumber ${ticketInfo.tempBackground}Back`;
  const cellClasses = `module ${ticketInfo.tempBackground}Back`;
  let longPressTimer = useRef<number | undefined>(undefined);

  const writeCells = (htmlElement: ChangeEvent<HTMLTextAreaElement>) => {
    const ticketsCopy = tickets.slice();

    ticketsCopy[rowIndex][colIndex].value = htmlElement.target.value.replace(
      "delta ",
      "\u0394 ",
    );

    changeTickets(ticketsCopy);
  };

  const setBold = () => {
    // start the timer and tell what to do at the end of the timer
    longPressTimer.current = window.setTimeout(() => {
      const ticketsCopy = tickets.slice();

      ticketsCopy[rowIndex][colIndex].bold =
        !ticketsCopy[rowIndex][colIndex].bold;
      changeTickets(ticketsCopy);
    }, 500);
  };

  const resetTimer = () => {
    clearTimeout(longPressTimer.current);
  };

  const changeColor = () => {
    const ticketsCopy = tickets.slice();

    ticketsCopy[rowIndex][colIndex].color = selectedColor;
    changeTickets(ticketsCopy);
  };

  const writeCNumber = (event: ChangeEvent<HTMLTextAreaElement>) => {
    const ticketsCopy = tickets.slice();

    ticketsCopy[rowIndex][colIndex].circuitNumber.value = event.target.value;
    changeTickets(ticketsCopy);
  };

  const setCNumberBold = () => {
    longPressTimer.current = window.setTimeout(() => {
      const ticketsCopy = tickets.slice();

      ticketsCopy[rowIndex][colIndex].circuitNumber.bold =
        !ticketsCopy[rowIndex][colIndex].circuitNumber.bold;
      changeTickets(ticketsCopy);
    }, 500);
  };

  const changeCNumberColor = () => {
    const ticketsCopy = tickets.slice();

    ticketsCopy[rowIndex][colIndex].circuitNumber.color = selectedColor;
    changeTickets(ticketsCopy);
  };

  return (
    <td key={colIndex} className={cellClasses} colSpan={ticketInfo.colspan}>
      <textarea
        key={`a${colIndex}`}
        className={circuitClasses}
        cols={5}
        placeholder="Circuit..."
        rows={7}
        style={{
          color: tickets[rowIndex][colIndex].color,
          fontWeight: ticketInfo.bold ? "bold" : "normal",
        }}
        value={ticketInfo.value}
        onChange={(event) => writeCells(event)}
        onDoubleClick={() => changeColor()}
        onMouseDown={() => setBold()}
        onMouseUp={resetTimer}
      />
      <br />
      <textarea
        key={`b${colIndex}`}
        className={circuitNumberClasses}
        cols={5}
        placeholder="N°"
        rows={1}
        style={{
          color: tickets[rowIndex][colIndex].circuitNumber.color,
          fontWeight: ticketInfo.circuitNumber.bold ? "bold" : "normal",
        }}
        value={ticketInfo.circuitNumber.value}
        onChange={(event) => writeCNumber(event)}
        onDoubleClick={() => changeCNumberColor()}
        onMouseDown={() => setCNumberBold()}
        onMouseUp={resetTimer}
      />
    </td>
  );
};

export default Ticket;
