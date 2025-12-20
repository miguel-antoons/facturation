import { useState, useEffect } from "react";
import "@/styles/tickets.css";
import "@/styles/printTickets.css";
import "@/styles/ticketCommands.css";
import { useLocation } from "react-router";
import { useParams } from "react-router-dom";
import { Input } from "@heroui/input";
import { Button } from "@heroui/button";
import { IoArrowDown, IoArrowUp } from "react-icons/io5";

import background from "@/assets/3840x2160-131329-abstract-green-and-white-low-poly-background.jpg";
import Row from "@/components/row";
import SaveStatus from "@/components/saveStatus.tsx";
import ReturnButton from "@/components/returnButton.tsx";
import PrintButton from "@/components/printButton.tsx";
import SaveButton from "@/components/saveButton.tsx";
import ClientAutocomplete from "@/components/clientAutocomplete.tsx";
import SwatchesPicker from "@/components/swatchesPicker.tsx";

const Tickets = () => {
  const [tickets, setTickets] = useState<
    {
      tempBackground: string;
      color: string;
      bold: boolean;
      colspan: number;
      value: string;
      circuitNumber: { color: string; bold: boolean; value: string };
    }[][]
  >([]); // contains the different characteristics of each row and cell in th table
  const [saved, setSaved] = useState(false); // indicates if the project is saved or not
  const [isLoadingTickets, setIsLoadingTickets] = useState(false); // indicates if the project is loading
  const [isLoadingCustomers, setIsLoadingCustomers] = useState(false);
  const [selectedTextColor, setSelectedTextColor] = useState("#ff0000"); // contains the selected text color)
  const [newLineColumns, setNewLineColumns] = useState(18); // contains the value of cells to add when a new row is requested
  const [projectID, setProjectID] = useState(Number(useParams().id)); // contains the project ID
  const [customerId, setCustomerId] = useState(""); // contains the customerId
  const [constructionSite, setConstructionSite] = useState(""); // contains the construction site of the project, this is shown on top of the page
  let { query } = useLocation(); // check if we have to print or not
  const [print, setPrint] = useState(query); // put the print variable in the state so that is not alwau-ys requested again

  /**
   * Function fires on page load and when new projectID is set
   */
  useEffect(() => {
    let initiateTable; // wil contain the function to call eventually

    // if there is a projectID greater than 0 (which means the project already existed)
    if (projectID) {
      /**
       * function will call an api to get the requested project
       */
      initiateTable = async () => {
        const response = await fetch("/api/etiquettes/" + projectID);
        const responseData = await response.json();

        // prepare the different states
        setProjectID(responseData.projectID);
        setCustomerId(responseData.clientID);
        setConstructionSite(responseData.constructionSite);
        setTickets(JSON.parse(responseData.projectData));
        // setSaved(<span className="saved">Enregistré</span>);

        // s'il faut imprimer, imprimer la page et mettre query à false pour ne pas réimprimer
        if (print) {
          printWindow();
          setPrint(false);
        }
      };
    }
    // if it is a newly created project
    else {
      /**
       * function adds a first row to the table.
       * this row can NEVER be deleted.
       * (one row contains 18 cells)
       */
      initiateTable = async () => {
        let tableContent: {
          tempBackground: string;
          color: string;
          bold: boolean;
          colspan: number;
          value: string;
          circuitNumber: { color: string; bold: boolean; value: string };
        }[][] = [[]];

        for (let i = 0; i < 18; i++) {
          tableContent[0].push({
            tempBackground: "",
            color: "black",
            bold: false,
            colspan: 2,
            value: "",
            circuitNumber: {
              color: "black",
              bold: false,
              value: "",
            },
          });
        }

        // set the different state values
        setTickets(tableContent);
        setSaved(false);

        // get the basic client information so that the user can choose a client to link this project
        try {
          const response = await fetch("/api/client");
          const responseData = await response.json();

        } catch (e) {
          console.log(e);
        }
      };
    }

    initiateTable();
  }, [projectID]);

  const changeTickets = (newTickets) => {
    setTickets(newTickets);
    setSaved(false);
  };

  /**
   * adds a row to the table, the new row will contain the number of columns
   * specified in the 'newLineColumns' state variable, this variable is changeable by the user.
   * The 'newLineColumns' value can't be greater than 18 and must at least be equal to 1
   */
  const addRow = () => {
    const ticketsCopy = tickets.slice();

    if (newLineColumns && newLineColumns <= 18) {
      // first push a new row to the state
      ticketsCopy.push([]);

      // then complete the row with the number of columns specified by the user (--> 'newLineColumns')
      for (let i = 0; i < newLineColumns; i++) {
        ticketsCopy[ticketsCopy.length - 1].push({
          tempBackground: "white",
          color: "black",
          bold: false,
          colspan: 2,
          value: "",
          circuitNumber: {
            color: "black",
            bold: false,
            value: "",
          },
        });
      }

      changeTickets(ticketsCopy);
    } else {
      // TODO show notification instead
    }
  };

  /**
   * deletes a row and all of its columns from the project state.
   * this function can be executed only if there are more than 1 rows left
   */
  const deleteRow = () => {
    if (tickets.length > 1) {
      const ticketsCopy = tickets.slice();

      ticketsCopy.pop();
      changeTickets(ticketsCopy);
    } else {
      // TODO use notification instead
    }
  };

  /**
   * function sends the project state to the backend server with the appropriate api.
   * The http method will either be POST if it is the first time the project is saved or
   * PUT if it isn't
   */
  const saveProject = async () => {
    // if all the input are correcctly specified (client and construction site)
    if (customerId && constructionSite) {
      // if there is already a prohjectID in which case it means the project already existed before
      if (projectID) {
        // try to put and, by doing so, update the project in the database
        try {
          await fetch("/api/etiquettes", {
            method: "put",
            headers: {
              "Content-type": "application/json",
            },
            body: JSON.stringify([constructionSite, tickets, projectID]),
          });
        } catch (e) {
          console.log(e);
        }
      }
      // if the project id equals to 0, it means the project didn't exist before and it has still to be created
      else {
        try {
          // send the data with the http POST method too create the new row in the database
          let response = await fetch("/api/etiquettes", {
            method: "post",
            headers: {
              "Content-type": "application/json",
            },
            body: JSON.stringify([customerId, constructionSite, tickets]),
          });

          // when the project is saved, wait for the project id to be returned and set the projectID state
          const responseData = await response.json();

          setProjectID(responseData.projectID);
        } catch (e) {
          console.log(e);
        }
      }
      setSaved(<span className="saved">Enregistré</span>);
    } else {
      // TODO use notification instead
    }
  };

  /**
   * Change css rules in order to adapt the css for printing,
   * and finally print the table
   */
  const printWindow = () => {
    let cssPagedMedia = (function () {
      let style = document.createElement("style");

      document.head.appendChild(style);

      return function (rule) {
        style.innerHTML = rule;
      };
    })();

    cssPagedMedia.size = function (size: string) {
      cssPagedMedia("@page {size: " + size + "}");
    };

    cssPagedMedia.size("A3 landscape");
    window.print();
  };

  return (
    <div
      className="flex flex-row no_margin programContainer"
      style={{ backgroundImage: `url(${background}` }}
    >
      <div className="no_print basis-3/12 p-10">
        <div className="flex flex-row pb-5">
          <div className="basis-1/2">
            <h1 className="text-xl font-bold text-white sm:truncate sm:tracking-tight">
              {"Nouvelle Étiquette"}
            </h1>
          </div>
          <div className="basis-1/2 flex justify-end">
            <SaveStatus
              isLoading={[isLoadingTickets, isLoadingCustomers]}
              saved={saved}
            />
          </div>
        </div>

        <div className="flex flex-row pb-5">
          <div className="basis-1/3">
            <ReturnButton />
          </div>
          <div className="basis-2/3 flex justify-end">
            <PrintButton printAction={() => printWindow()} />
            <SaveButton
              saveAction={() => console.log("saveButton")}
              saveStatus={saved}
            />
          </div>
        </div>

        <div className="flex flex-row pb-10">
          <div className="basis-1/1">
            <ClientAutocomplete
              color="success"
              customerId={customerId}
              setCustomerId={setCustomerId}
              setIsLoadingCustomers={setIsLoadingCustomers}
              size="lg"
            />
          </div>
        </div>

        <div className="flex flex-row pb-3">
          <div className="basis-1/1">
            <Input
              label="Colonnes à ajouter"
              max="20"
              min="5"
              step="1"
              type="number"
              value={String(newLineColumns)}
              onChange={(e) => setNewLineColumns(Number(e.target.value))}
            />
          </div>
        </div>
        <div className="flex flex-row pb-10">
          <div className="basis-1/2">
            <Button color="primary" radius="lg" size="lg" onPress={addRow}>
              <IoArrowDown size={20} /> Ajouter Ligne
            </Button>
          </div>
          <div className="basis-1/2 flex justify-end">
            <Button
              className="ml-2"
              color="danger"
              radius="lg"
              size="lg"
              onPress={deleteRow}
            >
              <IoArrowUp size={20} /> Supprimer Ligne
            </Button>
          </div>
        </div>

        <div className="flex flex-row pb-1">
          <h1 className="text-lg font-bold text-white sm:truncate sm:tracking-tight">
            Couleur de Texte
          </h1>
      </div>

        <div
          className="flex flex-row justify-center mb-10 p-6 rounded-4xl"
          style={{ backgroundColor: `${selectedTextColor}54` }}
        >
          <SwatchesPicker
            color={selectedTextColor}
            presetColors={["#000000", "#ff0000", "#008000", "#0000ff"]}
            onChange={setSelectedTextColor}
          />
        </div>
      </div>
      <div className="basis-9/12 justify-center no_margin p-10">
        <div className="flex flex-row justify-center no_margin">
          <input
            className="form-control form-control-lg constructionSite"
            placeholder="Chantier"
            type="text"
            value={constructionSite}
            onChange={(e) => {
              setConstructionSite(e.target.value);
            }}
          />
        </div>
        <div className="flex flex-row justify-center">
          <div className="etiquettesContainer">
            <table className="tableauxEtiquettes">
              <tbody className="etiquettes">
                {tickets.map((_row, rowIndex) => (
                  <Row
                    key={rowIndex}
                    changeTickets={changeTickets}
                    rowIndex={rowIndex}
                    selectedColor={selectedTextColor}
                    setTickets={setTickets}
                    tickets={tickets}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Tickets;
