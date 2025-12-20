import React from "react";

import Ticket from "@/components/ticket";

import "@/styles/tickets.css";
import "@/styles/ticketCommands.css";

const Row = ({
  tickets,
  rowIndex,
  changeTickets,
  selectedColor,
  setTickets,
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
  setTickets: (
    newTickets: {
      tempBackground: string;
      color: string;
      bold: boolean;
      colspan: number;
      value: string;
      circuitNumber: { color: string; bold: boolean; value: string };
    }[][],
  ) => void;
}) => {
  const rowContent = tickets[rowIndex];

  const fuseMergeCells = (
    event: React.MouseEvent<HTMLTableCellElement, MouseEvent>,
    colIndex: number,
  ) => {
    event.preventDefault();
    const ticketsCopy = tickets.slice();
    let newColumnColspan;

    // if the click is a right click and the colspan is greater than 1
    if (event.button === 2 && ticketsCopy[rowIndex][colIndex].colspan > 1) {
      // divide the column in 2 parts and generate a new column
      newColumnColspan = Math.floor(
        ticketsCopy[rowIndex][colIndex].colspan / 2,
      );
      ticketsCopy[rowIndex].splice(colIndex + 1, 0, {
        tempBackground: "white",
        color: "black",
        bold: false,
        colspan: newColumnColspan,
        value: "",
        circuitNumber: {
          color: "black",
          bold: false,
          value: "",
        },
      });

      // decrease the colspan of the existing column
      ticketsCopy[rowIndex][colIndex].colspan -= newColumnColspan;
    }
    // if the click is a left click and there are more than 1 column left in the row
    else if (event.button === 0 && ticketsCopy[rowIndex].length > 1) {
      // increase the left column with the right column's colspan
      ticketsCopy[rowIndex][colIndex].colspan +=
        ticketsCopy[rowIndex][colIndex + 1].colspan;
      // delete the right column
      ticketsCopy[rowIndex].splice(colIndex + 1, 1);
    }

    changeTickets(ticketsCopy);
    clearPreview();
    fuseMergePreview(colIndex);
  };

  const fuseMergePreview = (colIndex: number) => {
    let ticketsCopy = tickets.slice();

    // set different colors depending on the column index and the number of columns
    if (
      colIndex === ticketsCopy[rowIndex].length - 1 &&
      ticketsCopy[rowIndex][colIndex].colspan <= 1
    ) {
      ticketsCopy[rowIndex][colIndex].tempBackground = "green";
    } else if (colIndex === ticketsCopy[rowIndex].length - 1) {
      ticketsCopy[rowIndex][colIndex].tempBackground = "red";
    } else if (ticketsCopy[rowIndex][colIndex].colspan === 1) {
      ticketsCopy[rowIndex][colIndex].tempBackground = "green";
      ticketsCopy[rowIndex][colIndex + 1].tempBackground = "green";
    } else {
      ticketsCopy[rowIndex][colIndex].tempBackground = "red";
      ticketsCopy[rowIndex][colIndex + 1].tempBackground = "green";
    }

    setTickets(ticketsCopy);
  };

  const clearPreview = () => {
    const ticketsCopy = tickets.slice();

    for (let e of ticketsCopy[rowIndex]) {
      e.tempBackground = "";
    }

    setTickets(ticketsCopy);
  };

  return (
    <>
      <tr className="bg-linear-to-r from-yellow-200 via-lime-400 to-green-600 fuseMergeRow">
        {rowContent.map((column, colIndex) => (
          <td
            key={colIndex}
            className="fuseMergeCell"
            colSpan={column.colspan}
            onClick={(event) => fuseMergeCells(event, colIndex)}
            onContextMenu={(event) => fuseMergeCells(event, colIndex)}
            onMouseOut={() => clearPreview()}
            onMouseOver={() => fuseMergePreview(colIndex)}
          >
            {colIndex ? "" : rowIndex + 1}
          </td>
        ))}
      </tr>
      <tr className="ticket">
        {rowContent.map((_column, colIndex) => (
          <Ticket
            key={colIndex}
            changeTickets={changeTickets}
            colIndex={colIndex}
            rowIndex={rowIndex}
            selectedColor={selectedColor}
            tickets={tickets}
          />
        ))}
      </tr>
    </>
  );
};

export default Row;
