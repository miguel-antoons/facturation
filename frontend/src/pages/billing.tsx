import { Input } from "@heroui/input";
import { useEffect, useState } from "react";
import { Select, SelectItem } from "@heroui/select";
import { Button } from "@heroui/button";
import {
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  useDisclosure,
} from "@heroui/modal";
import { Autocomplete, AutocompleteItem } from "@heroui/autocomplete";
import { useNavigate, useParams } from "react-router-dom";
import { getLocalTimeZone, today, parseDate } from "@internationalized/date";
import { I18nProvider } from "@react-aria/i18n";
import { DatePicker } from "@heroui/date-picker";
import { addToast } from "@heroui/toast";
import { IoArrowDown, IoArrowUp } from "react-icons/io5";

import OrderLine from "@/components/orderLine.tsx";
import SendPeppolButton from "@/components/sendPeppolButton.tsx";
import SaveStatus from "@/components/saveStatus.tsx";
import ReturnButton from "@/components/returnButton.tsx";
import PrintButton from "@/components/printButton.tsx";
import SaveButton from "@/components/saveButton.tsx";

const Billing = () => {
  const [billId, setBillId] = useState(Number(useParams().id));
  const [shownBillId, setShownBillId] = useState("");
  const [billNumber, setBillNumber] = useState("");
  const [heading, setHeading] = useState(""); // heading of the page
  const [customerId, setCustomerId] = useState("");
  const [orderTitle, setOrderTitle] = useState("");
  const [orderDate, setOrderDate] = useState(today(getLocalTimeZone()));
  const [expiryDate, setExpiryDate] = useState(
    today(getLocalTimeZone()).add({ days: 14 }),
  );
  const [deliveryDate, setDeliveryDate] = useState(today(getLocalTimeZone()));
  const vatOptions = [
    { value: "1", label: "0%", key: "1" },
    { value: "2", label: "6%", key: "2" },
    { value: "4", label: "21%", key: "4" },
    { value: "21", label: "Co-contractant", key: "21" },
  ];
  const reverseVat: { [index: string]: number } = {
    "1": 0.0,
    "2": 6.0,
    "4": 21.0,
    "21": 0.0,
  };
  const [vat, setVat] = useState(vatOptions[2].value);
  const [orderLines, setOrderLines] = useState([
    { key: 0, description: "", quantity: "1", unitPrice: "0.0", unit: "" },
  ]);
  const [customers, setCustomers] = useState([]);
  const [isLoadingBill, setIsLoadingBill] = useState(false); // loading state of the page
  const [isLoadingCustomers, setIsLoadingCustomers] = useState(false); // loading state of the page
  const [saved, setSaved] = useState(false); // save icon state of the page
  const [modalText, setModalText] = useState(<></>); // text to display in the modal
  const [printing, setPrinting] = useState(false); // printing state of the page
  const [emailPresent, setEmailPresent] = useState<{ [key: string]: boolean }>(
    {},
  );
  const [clientHasVat, setClientHasVat] = useState<{ [key: string]: boolean }>(
    {},
  );
  const [lastSave, setLastSave] = useState({});
  const navigate = useNavigate(); // navigate function from react router
  const [isSent, setIsSent] = useState<boolean>(false);
  const { isOpen, onOpen, onOpenChange } = useDisclosure(); // modal state from heroui

  /**
   * Fetch the bill data if editing an existing bill
   */
  useEffect(() => {
    if (billId !== 0 && billId !== undefined) {
      setIsLoadingBill(true);
      fetch(`/api/bills/${billId}`)
        .then((response) => response.json())
        .then((data) => {
          // set the state with the fetched data
          setShownBillId(data.OrderNumber);
          setBillNumber(data.OrderNumber);
          setCustomerId(data.CounterParty.Nr);
          setOrderTitle(data.OrderTitle);
          setOrderDate(parseDate(data.OrderDate.split("T")[0]));
          setExpiryDate(parseDate(data.ExpiryDate.split("T")[0]));
          setDeliveryDate(parseDate(data.DeliveryDate.split("T")[0]));
          setVat(data.VentilationCode);
          setIsSent(
            data.CurrentDocumentDeliveryDetails.IsDocumentDelivered ||
              data.CurrentDocumentDeliveryDetails.DocumentDeliveryStatus ===
                "Pending",
          );
          setOrderLines(
            data.OrderLines.map((line: any, index: number) => ({
              key: index,
              description: line.Description,
              quantity: line.Quantity,
              unitPrice: line.UnitPriceExcl,
              unit: line.Unit,
            })),
          );
          setSaved(true);
          setIsLoadingBill(false);
          setLastSave(
            JSON.stringify({
              customerId: data.CounterParty.Nr,
              orderTitle: data.OrderTitle,
              orderDate: parseDate(data.OrderDate.split("T")[0]),
              billNumber: data.OrderNumber,
              expiryDate: parseDate(data.ExpiryDate.split("T")[0]),
              deliveryDate: parseDate(data.DeliveryDate.split("T")[0]),
              vat: data.VentilationCode,
              orderLines: data.OrderLines.map((line: any, index: number) => ({
                key: index,
                description: line.Description,
                quantity: line.Quantity,
                unitPrice: String(line.UnitPriceExcl),
                unit: line.Unit,
              })),
            }),
          );
        })
        .catch((e) => {
          addToast({
            title: "Erreur",
            description:
              "Impossible de retrouver les informations de la facture. Veuillez réessayer plus tard.",
            color: "danger",
          });
          // eslint-disable-next-line
          console.log(e);
          setIsLoadingBill(false);
        });
    }
  }, [billId]);

  /**
   * Fetch the customers for the autocomplete
   */
  useEffect(() => {
    // get the clients for the autocomplete
    setIsLoadingCustomers(true);
    fetch("/api/customers")
      .then((response) => response.json())
      .then((data) => {
        const formattedData: {
          label: string;
          key: string;
        }[] = [];
        const emailDict: { [key: string]: boolean } = {};
        const vatDict: { [key: string]: boolean } = {};

        // sort data based on id
        data.sort((a: { id: number }, b: { id: number }) => a.id - b.id);

        data.forEach(
          (element: {
            id: number;
            company: string;
            name: string;
            surname: string;
            hasEmail: boolean;
            hasVAT: boolean;
          }) => {
            if (
              element.id === 0 ||
              element.id === undefined ||
              element.id === null
            )
              return;
            let label: string;

            if (element.name === null && element.surname === null) {
              label = element.company === null ? "N/A" : element.company;
            } else if (element.company === null) {
              label = `${element.name === null ? "" : element.name} ${element.surname === null ? "" : element.surname}`;
            } else {
              label = `${element.name === null ? "" : element.name} ${element.surname === null ? "" : element.surname}, ${element.company}`;
            }
            label = `${element.id}, ${label}`;
            formattedData.push({
              label: label,
              key: String(element.id),
            });
            emailDict[String(element.id)] = element.hasEmail;
            vatDict[String(element.id)] = element.hasVAT;
          },
        );
        // @ts-ignore
        setCustomers(formattedData);
        setEmailPresent(emailDict);
        setClientHasVat(vatDict);
        setIsLoadingCustomers(false);
      })
      .catch((e) => {
        addToast({
          title: "Erreur",
          description:
            "Impossible de retrouver la liste de clients. Veuillez réessayer plus tard.",
          color: "danger",
        });
        // eslint-disable-next-line
        console.log(e);
        setIsLoadingBill(false);
      });
  }, []);

  /**
   * Set the heading based on the billId
   */
  useEffect(() => {
    // set heading based on billId
    if (billId === 0 || billId === undefined) {
      setHeading("Nouvelle Facture");
    } else {
      setHeading(`Facture Numéro ${shownBillId}`);
    }
  }, [billId, shownBillId]);

  /**
   * Add a new empty order line
   */
  const addLine = () => {
    const orderLinesSlice = orderLines.slice();

    orderLinesSlice.push({
      key: orderLines.length,
      description: "",
      quantity: "1",
      unitPrice: "0.0",
      unit: "",
    });
    change(setOrderLines, orderLinesSlice);
  };

  /**
   * Delete the last order line if there is more than one
   */
  const delLine = () => {
    if (orderLines.length === 1) return; // do nothing if only one line
    const orderLinesSlice = orderLines.slice(0, -1);

    change(setOrderLines, orderLinesSlice);
  };

  /**
   * Write a value to an order line cell
   * @param index - index of the order line
   * @param attribute - attribute to write (description, quantity, unitPrice, unit)
   * @param value - value to write
   */
  const writeOrderCell = (
    index: number,
    attribute: string,
    value: string | number,
  ) => {
    const orderLinesSlice = orderLines.slice();

    // @ts-ignore
    orderLinesSlice[index][attribute] = value;
    setOrderLines(orderLinesSlice);
    setSaved(false);
  };

  /**
   * Check if the current state is different from the last saved state
   * @returns true if different, false if same
   */
  const isDifferentFromLastSave = () => {
    return (
      JSON.stringify({
        customerId,
        orderTitle,
        orderDate,
        billNumber,
        expiryDate,
        deliveryDate,
        vat,
        orderLines,
      }) !== lastSave
    );
  };

  /**
   * Verify the data before saving
   * If any required field is missing, show a modal
   * If printMe is true, print the document after saving
   * @param printMe - whether to print the document after saving
   */
  const verifyAndSave = (printMe = false) => {
    // function to verify the data before saving
    setModalText(<></>);
    if (customerId === "") {
      // at least one of lastName, surname or company must be filled
      addToast({
        title: "Erreur",
        description: "Veuillez entrer au moins un nom, prénom ou une société.",
        color: "danger",
      });

      return;
    }

    const orderTitleMissing = orderTitle === "";
    const datesMismatch = expiryDate < orderDate;
    // @ts-ignore
    const missingEmail = !emailPresent[customerId]; // email must be present in comment
    const missingVat = vat === "";

    // create modal text based on missing fields
    const modalText = (
      <>
        {orderTitleMissing ? (
          <p>L&lsquo;objet de la facture est manquante.</p>
        ) : null}
        {datesMismatch ? (
          <p>
            La date d&lsquo;échéance est avant la date de facture. Veuillez vous
            assurez que les dates sont correctes.
          </p>
        ) : null}
        {missingEmail ? (
          <p>
            Aucun email n&lsquo;a été trouvé pour ce client. Pour en ajouter un,
            ajoutez un email dans le commentaire du client, puis ré-enregistrez
            cette facture.
          </p>
        ) : null}
        {missingVat ? <p>Le pourcentage de TVA est manquant.</p> : null}
        <p>
          <b>Êtes vous sur de vouloir continuer?</b>
        </p>
      </>
    );

    if (orderTitleMissing || datesMismatch || missingEmail || missingVat) {
      setPrinting(printMe);
      // if any of the above conditions are true, show modal
      setModalText(modalText);
      onOpen();

      return;
    }

    saveChanges(printMe);
  };

  /**
   * Save changes to the backend
   * If printMe is true, print the document after saving
   * @param printMe - whether to print the document after saving
   */
  const saveChanges = (printMe = false) => {
    const differentFromLastSave = isDifferentFromLastSave();

    if (!differentFromLastSave) setSaved(true);
    // if already loading, do nothing (prevents double click)
    if ((isLoadingBill || !differentFromLastSave) && printMe)
      printElement(Number(billId));
    if (isLoadingBill || !differentFromLastSave) return;

    setIsLoadingBill(true);
    const billData = {
      customerId: Number(customerId),
      orderTitle: orderTitle,
      orderDate: orderDate.toString(),
      expiryDate: expiryDate.toString(),
      deliveryDate: deliveryDate.toString(),
      orderNumber: billNumber === "" ? null : billNumber,
      ventilationCode: vat,
      orderLines: orderLines.map((line) => ({
        description: line.description,
        quantity: Number(line.quantity),
        unitPriceExcl: Number(line.unitPrice),
        unit: line.unit,
        VATPercentage: reverseVat[vat],
      })),
    };

    // define behavior on success
    const onSuccess = (id: number) => {
      setShownBillId(billNumber);
      if (billId === 0 || billId === undefined) navigate(`/bill/${id}`);
      if (printMe) printElement(id);
      if (id !== billId) setBillId(id);
      setSaved(true);
      setLastSave(
        JSON.stringify({
          customerId,
          orderTitle,
          orderDate,
          billNumber,
          expiryDate,
          deliveryDate,
          vat,
          orderLines,
        }),
      );
      setIsLoadingBill(false);
      addToast({
        title: "Facture Enregistrée",
        description: `La facture numéro ${id} a été enregistrée avec succès.`,
        color: "success",
      });
    };

    // define behavior on failure
    const onFailure = (error: any) => {
      setIsLoadingBill(false);
      addToast({
        title: "Erreur",
        description:
          "Impossible d'enregistrer la facture. Veuillez réessayer plus tard.",
        color: "danger",
      });
      // eslint-disable-next-line
      console.log(error);
    };

    const method = billId === 0 || billId === undefined ? "POST" : "PUT";
    const url =
      billId === 0 || billId === undefined
        ? "/api/bills"
        : `/api/bills/${billId}`;

    fetch(url, {
      method: method,
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(billData),
    })
      .then((response) => response.json())
      .then((data: { status: string; id: number; message: string }) => {
        if (data.status === "failed") onFailure(data.message);
        else onSuccess(data.id);
      })
      .catch((error) => onFailure(error));
  };

  /**
   * Print the element with the given id
   * @param id - id of the element to print
   */
  const printElement = async (id: number) => {
    const response = await fetch(`/api/files/bills/${id}`, {
      method: "GET",
    });

    // print pdf
    const blob = await response.blob();
    const fileURL = URL.createObjectURL(blob);
    // print in new tab
    const w = window.open(fileURL);

    if (!w) {
      addToast({
        title: "Erreur lors de l'Impression",
        description:
          "Impossible d'ouvrir une nouvelle fenêtre pour l'impression.",
        color: "danger",
      });

      return;
    }
    w.print();
  };

  // generic change function to set saved to false on any change
  // fun is the set function, value is the new value
  // example: change(setOrderTitle, e.target.value)
  const change = (fun: (val: any) => void, value: any) => {
    fun(value);
    setSaved(false);
  };

  return (
    <>
      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-3/4 md:basis-3/8 p-2">
          <h1 className="text-2xl/7 font-bold text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            {heading}
          </h1>
        </div>
        <div className="basis-1/4 md:basis-1/8 p-2 flex justify-end">
          <SaveStatus
            isLoading={[isLoadingBill, isLoadingCustomers]}
            saved={saved}
          />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <Modal isOpen={isOpen} onOpenChange={onOpenChange}>
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader className="flex flex-col gap-1">
                Attention!
              </ModalHeader>
              <ModalBody>{modalText}</ModalBody>
              <ModalFooter>
                <Button
                  color="default"
                  onPress={() => {
                    onClose();
                    setPrinting(false);
                    setModalText(<></>);
                  }}
                >
                  Non, Annuler
                </Button>
                {printing ? (
                  <Button
                    color="success"
                    onPress={() => {
                      onClose();
                      setPrinting(false);
                      setModalText(<></>);
                      saveChanges(true);
                    }}
                  >
                    Oui, Continuer
                  </Button>
                ) : (
                  <Button
                    color="success"
                    onPress={() => {
                      onClose();
                      setModalText(<></>);
                      saveChanges(false);
                    }}
                  >
                    Oui, Continuer
                  </Button>
                )}
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/3 md:basis-1/6 p-2">
          <ReturnButton to="/billlist" />
        </div>
        <div className="basis-2/3 md:basis-2/6 p-2 flex justify-end">
          <SendPeppolButton
            billSaved={saved}
            clientHasVAT={
              customerId !== "0" || customerId === undefined
                ? clientHasVat[customerId]
                : false
            }
            isAlreadySent={isSent}
            orderId={billId}
            setIsAlreadySent={setIsSent}
          />
          <PrintButton
            printAction={() => {
              verifyAndSave(true);
            }}
          />
          <SaveButton saveAction={() => verifyAndSave()} saveStatus={saved} />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/1 md:basis-4/8 p-2">
          <Autocomplete
            defaultItems={customers}
            label="Choisissez un Client"
            selectedKey={String(customerId)}
            // @ts-ignore
            onSelectionChange={(event) => setCustomerId(event)}
          >
            {(customer) => (
              // @ts-ignore
              <AutocompleteItem key={customer.key}>
                {
                  // @ts-ignore
                  customer.label
                }
              </AutocompleteItem>
            )}
          </Autocomplete>
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/1 md:basis-4/8 p-2">
          <Input
            label="Numéro de Facture"
            type="text"
            value={billNumber}
            onChange={(e) => change(setBillNumber, e.target.value)}
          />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/1 md:basis-4/8 p-2">
          <Input
            label="Objet de la Facture"
            type="text"
            value={orderTitle}
            onChange={(e) => change(setOrderTitle, e.target.value)}
          />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/3 md:basis-1/6 p-2">
          <I18nProvider locale="fr-FR">
            <DatePicker
              firstDayOfWeek="mon"
              label="Date Fin Travaux"
              value={deliveryDate}
              onChange={(e) => change(setDeliveryDate, e)}
            />
          </I18nProvider>
        </div>
        <div className="basis-1/3 md:basis-1/6 p-2">
          <I18nProvider locale="fr-FR">
            <DatePicker
              firstDayOfWeek="mon"
              label="Date Facture"
              value={orderDate}
              onChange={(e) => change(setOrderDate, e)}
            />
          </I18nProvider>
        </div>
        <div className="basis-1/3 md:basis-1/6 p-2">
          <I18nProvider locale="fr-FR">
            <DatePicker
              firstDayOfWeek="mon"
              label="Date Échéance"
              value={expiryDate}
              onChange={(e) => change(setExpiryDate, e)}
            />
          </I18nProvider>
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/1 md:basis-4/8 p-2">
          <Select
            // @ts-ignore
            classNames="max-w-xs"
            label="TVA"
            selectedKeys={[String(vat)]}
            onChange={(event) => change(setVat, event.target.value)}
          >
            {vatOptions.map((option) => (
              // @ts-ignore
              <SelectItem key={option.key} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </Select>
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      {orderLines.map((line, index) => (
        <OrderLine
          key={index}
          lineNumber={index + 1}
          orderInfo={line}
          writeOrderCell={writeOrderCell}
        />
      ))}

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/2 md:basis-1/4 p-2">
          <Button color="primary" radius="lg" onPress={addLine}>
            <IoArrowDown size={20} /> Ajouter Ligne
          </Button>
          <Button className="ml-2" color="danger" radius="lg" onPress={delLine}>
            <IoArrowUp size={20} /> Supprimer Ligne
          </Button>
        </div>
        <div className="basis-1/2 md:basis-1/4 p-2 flex justify-end">
          <PrintButton
            printAction={() => {
              verifyAndSave(true);
            }}
          />
          <SaveButton saveAction={() => verifyAndSave()} saveStatus={saved} />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>
    </>
  );
};

export default Billing;
