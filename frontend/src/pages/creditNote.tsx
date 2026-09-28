import { Input } from "@heroui/input";
import { useEffect, useState } from "react";
import { Select, SelectItem } from "@heroui/select";
import { Button } from "@heroui/button";
import { useDisclosure } from "@heroui/modal";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
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
import ClientAutocomplete from "@/components/clientAutocomplete.tsx";
import FormConfirmModal from "@/components/formConfirmModal.tsx";
import {
  cnoteIsBillitReady,
  isPeppolReady,
  isSaveReady,
} from "@/utils/validation.ts";
import { isSentToPeppol } from "@/utils/peppol.ts";
import SendBillitButton from "@/components/sendBillitButton.tsx";

const CreditNote = () => {
  const [searchParams] = useSearchParams();
  const [cnoteId, setCnoteId] = useState(String(useParams().id));
  const [shownCnoteId, setShownCnoteId] = useState("");
  const [cnoteNumber, setCnoteNumber] = useState(
    `C${searchParams.get("bill") || ""}`,
  );
  const [billNumber, setBillNumber] = useState(searchParams.get("bill") || "");
  const [heading, setHeading] = useState(""); // heading of the page
  const [customerId, setCustomerId] = useState(
    searchParams.get("customerId") || "",
  );
  const [orderTitle, setOrderTitle] = useState(searchParams.get("title") || "");
  const [orderDate, setOrderDate] = useState(today(getLocalTimeZone()));
  const [expiryDate, setExpiryDate] = useState(
    today(getLocalTimeZone()).add({ days: 14 }),
  );
  const vatOptions = [
    // { value: "1", label: "0%", key: "1" },
    { value: "2", label: "6%", key: "2" },
    { value: "4", label: "21%", key: "4" },
    { value: "21", label: "Co-contractant", key: "21" },
  ];
  const reverseVat: { [index: string]: number } = {
    // "1": 0.0,
    "2": 6.0,
    "4": 21.0,
    "21": 0.0,
  };
  const [vat, setVat] = useState(
    searchParams.get("ventilationCode") || vatOptions[1].value,
  );
  const [orderLines, setOrderLines] = useState([
    { key: 0, description: "", quantity: "1", unitPrice: "0.0", unit: "" },
  ]);
  const [isLoadingCnote, setIsLoadingCnote] = useState(false); // loading state of the page
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
  const [peppolDeliveryStatus, setPeppolDeliveryStatus] = useState<number>(0);
  const [billitSent, setBillitSent] = useState<boolean>(false);
  const { isOpen, onOpen, onOpenChange } = useDisclosure(); // modal state from heroui

  const [saveDisabled, setSaveDisabled] = useState(true);
  const [saveTooltip, setSaveTooltip] = useState("");

  const [billitDisabled, setBillitDisabled] = useState(true);
  const [billitTooltip, setBillitTooltip] = useState("");

  const [peppolDisabled, setPeppolDisabled] = useState(true);
  const [peppolTooltip, setPeppolTooltip] = useState("");

  /**
   * Fetch the cnote data if editing an existing cnote
   */
  useEffect(() => {
    if (cnoteId !== "0" && cnoteId !== undefined) {
      setIsLoadingCnote(true);
      fetch(`/api/cnotes/${cnoteId}`)
        .then((response) => response.json())
        .then(
          (data: {
            orderNumber: string;
            customerId: string;
            orderTitle: string;
            orderDate: string;
            expiryDate: string;
            deliveryDate: string;
            ventilationCode: string;
            billitSent: boolean;
            peppolDeliveryStatus: number;
            aboutInvoiceNumber: string;
            orderLines: {
              description: string;
              quantity: number;
              unitPriceExcl: number;
              unit: string;
            }[];
          }) => {
            // set the state with the fetched data
            setShownCnoteId(data.orderNumber);
            setCnoteNumber(data.orderNumber);
            setBillNumber(data.aboutInvoiceNumber);
            setCustomerId(data.customerId);
            setOrderTitle(data.orderTitle);
            setOrderDate(parseDate(data.orderDate.split("T")[0]));
            setExpiryDate(parseDate(data.expiryDate.split("T")[0]));
            setVat(data.ventilationCode);
            setBillitSent(data.billitSent);
            setPeppolDeliveryStatus(data.peppolDeliveryStatus);
            setOrderLines(
              data.orderLines.map((line: any, index: number) => ({
                key: index,
                description: line.description,
                quantity: line.quantity,
                unitPrice: line.unitPriceExcl,
                unit: line.unit,
              })),
            );
            setSaved(true);
            setIsLoadingCnote(false);
            setLastSave(
              JSON.stringify({
                customerId: data.customerId,
                orderTitle: data.orderTitle,
                orderDate: parseDate(data.orderDate.split("T")[0]),
                cnoteNumber: data.orderNumber,
                billNumber: data.aboutInvoiceNumber,
                expiryDate: parseDate(data.expiryDate.split("T")[0]),
                vat: data.ventilationCode,
                orderLines: data.orderLines.map((line: any, index: number) => ({
                  key: index,
                  description: line.description.replace(/\r/g, ""),
                  quantity: line.quantity,
                  unitPrice: String(line.unitPriceExcl),
                  unit: line.unit,
                })),
              }),
            );
          },
        )
        .catch((e) => {
          addToast({
            title: "Erreur",
            description:
              "Impossible de retrouver les informations de la note de crédit. Veuillez réessayer plus tard.",
            color: "danger",
          });
          // eslint-disable-next-line
          console.log(e);
          setIsLoadingCnote(false);
        });
    }
  }, [cnoteId]);

  useEffect(() => {
    const saveButtonInfo = isSaveReady(
      customerId,
      orderTitle,
      cnoteNumber,
      billitSent,
    );

    setSaveDisabled(saveButtonInfo.disabled);
    setSaveTooltip(saveButtonInfo.tooltipText);
  }, [customerId, orderTitle, billNumber, billitSent]);

  useEffect(() => {
    const billitButtonInfo = cnoteIsBillitReady(
      saved,
      orderLines,
      billitSent,
      billNumber,
    );

    setBillitDisabled(billitButtonInfo.disabled);
    setBillitTooltip(billitButtonInfo.tooltipText);
  }, [saved, orderLines, billitSent, billNumber]);

  useEffect(() => {
    const clientChosenAndHasVat =
      customerId !== "0" || customerId === undefined
        ? clientHasVat[customerId]
        : false;
    const peppolButtonInfo = isPeppolReady(
      billitSent,
      clientChosenAndHasVat,
      isSentToPeppol(peppolDeliveryStatus),
    );

    setPeppolDisabled(peppolButtonInfo.disabled);
    setPeppolTooltip(peppolButtonInfo.tooltipText);
  }, [billitSent, clientHasVat, customerId, peppolDeliveryStatus]);

  /**
   * Set the heading based on the cnoteId
   */
  useEffect(() => {
    // set heading based on cnoteId
    if (cnoteId === "0" || cnoteId === undefined) {
      setHeading("Nouvelle Note de Crédit");
    } else {
      setHeading(`Note de Crédit Numéro ${shownCnoteId}`);
    }
  }, [cnoteId, shownCnoteId]);

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
        cnoteNumber,
        billNumber,
        expiryDate,
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
        description: "Veuillez choisir un client.",
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
          <p>L&lsquo;objet de la note de crédit est manquante.</p>
        ) : null}
        {datesMismatch ? (
          <p>
            La date d&lsquo;échéance est avant la date de note de crédit.
            Veuillez vous assurez que les dates sont correctes.
          </p>
        ) : null}
        {missingEmail ? (
          <p>
            Aucun email n&lsquo;a été trouvé pour ce client. Pour en ajouter un,
            ajoutez un email dans le commentaire du client, puis ré-enregistrez
            cette note de crédit.
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
    if ((isLoadingCnote || !differentFromLastSave || billitSent) && printMe)
      printElement(cnoteId);
    if (isLoadingCnote || !differentFromLastSave || billitSent) return;

    setIsLoadingCnote(true);
    const cnoteData = {
      customerId: Number(customerId),
      orderTitle: orderTitle,
      orderDate: orderDate.toString(),
      expiryDate: expiryDate.toString(),
      orderNumber: cnoteNumber === "" ? null : cnoteNumber,
      aboutInvoiceNumber: billNumber === "" ? null : billNumber,
      ventilationCode: vat,
      orderLines: orderLines.map((line) => ({
        description: line.description.replace(/\r/g, ""),
        quantity: Number(line.quantity),
        unitPriceExcl: Number(line.unitPrice),
        unit: line.unit,
        VATPercentage: reverseVat[vat],
      })),
    };

    // define behavior on success
    const onSuccess = (id: string) => {
      setShownCnoteId(cnoteNumber);
      if (cnoteId === "0" || cnoteId === undefined)
        navigate(`/cnote/${id}`, { replace: true });
      if (printMe) printElement(id);
      if (id !== cnoteId) setCnoteId(id);
      setSaved(true);
      setLastSave(
        JSON.stringify({
          customerId,
          orderTitle,
          orderDate,
          cnoteNumber,
          billNumber,
          expiryDate,
          vat,
          orderLines,
        }),
      );
      setIsLoadingCnote(false);
      addToast({
        title: "Note de Crédit Enregistrée",
        description: `La note de crédit numéro ${cnoteNumber} a été enregistrée avec succès.`,
        color: "success",
      });
    };

    // define behavior on failure
    const onFailure = (error: any) => {
      setIsLoadingCnote(false);
      addToast({
        title: "Erreur",
        description:
          "Impossible d'enregistrer la note de crédit. Veuillez réessayer plus tard.",
        color: "danger",
      });
      // eslint-disable-next-line
      console.log(error);
    };

    const method = cnoteId === "0" || cnoteId === undefined ? "POST" : "PUT";
    const url =
      cnoteId === "0" || cnoteId === undefined
        ? "/api/cnotes"
        : `/api/cnotes/${cnoteId}`;

    fetch(url, {
      method: method,
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(cnoteData),
    })
      .then((response) => response.json())
      .then((data: { status: string; id: string; message: string }) => {
        if (data.status === "error") onFailure(data.message);
        else onSuccess(data.id);
      })
      .catch((error) => onFailure(error));
  };

  /**
   * Print the element with the given id
   * @param id - id of the element to print
   */
  const printElement = async (id: string) => {
    const response = await fetch(`/api/files/cnotes/${id}`, {
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
            isLoading={[isLoadingCnote, isLoadingCustomers]}
            saved={saved}
          />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <FormConfirmModal
        isOpen={isOpen}
        modalText={modalText}
        printing={printing}
        saveChanges={saveChanges}
        setModalText={setModalText}
        setPrinting={setPrinting}
        onOpenChange={onOpenChange}
      />

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/4 md:basis-1/8 p-2">
          <ReturnButton />
        </div>
        <div className="basis-3/4 md:basis-3/8 p-2 flex justify-end">
          <SendBillitButton
            apiRoute={`/api/cnotes/sendBillit/`}
            isDisabled={billitDisabled}
            isSent={billitSent}
            orderId={cnoteId}
            orderSaved={saved}
            setIsSent={setBillitSent}
            toolTipText={billitTooltip}
          />
          <SendPeppolButton
            apiRoute={`/api/cnotes/sendPeppol/`}
            isDisabled={peppolDisabled}
            orderId={cnoteId}
            peppolStatus={peppolDeliveryStatus}
            setPeppolStatus={setPeppolDeliveryStatus}
            tooltipText={peppolTooltip}
          />
          <PrintButton
            printAction={() => {
              verifyAndSave(true);
            }}
          />
          <SaveButton
            isDisabled={saveDisabled}
            isLoading={isLoadingCnote}
            isSaved={saved}
            saveAction={() => verifyAndSave()}
            tooltipText={saveTooltip}
          />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/1 md:basis-4/8 p-2">
          <ClientAutocomplete
            customerId={customerId}
            isDisabled={billitSent}
            setClientHasVat={setClientHasVat}
            setCustomerId={(newVal: string) => change(setCustomerId, newVal)}
            setEmailPresent={setEmailPresent}
            setIsLoadingCustomers={setIsLoadingCustomers}
          />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/1 md:basis-4/8 p-2">
          <Input
            isDisabled={billitSent}
            label="Numéro de Note de Crédit"
            type="text"
            value={cnoteNumber}
            onChange={(e) => change(setCnoteNumber, e.target.value)}
          />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/1 md:basis-4/8 p-2">
          <Input
            isDisabled={billitSent}
            label="Numéro de Facture Concernée"
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
            isDisabled={billitSent}
            label="Objet de la Note de Crédit"
            type="text"
            value={orderTitle}
            onChange={(e) => change(setOrderTitle, e.target.value)}
          />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/2 md:basis-1/4 p-2">
          <I18nProvider locale="fr-FR">
            <DatePicker
              firstDayOfWeek="mon"
              isDisabled={billitSent}
              label="Date Note de Crédit"
              value={orderDate}
              onChange={(e) => change(setOrderDate, e)}
            />
          </I18nProvider>
        </div>
        <div className="basis-1/2 md:basis-1/4 p-2">
          <I18nProvider locale="fr-FR">
            <DatePicker
              firstDayOfWeek="mon"
              isDisabled={billitSent}
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
            isDisabled={billitSent}
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
          isDisabled={billitSent}
          lineNumber={index + 1}
          orderInfo={line}
          writeOrderCell={writeOrderCell}
        />
      ))}

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/2 md:basis-1/4 p-2">
          <Button
            color="primary"
            isDisabled={billitSent}
            radius="lg"
            onPress={addLine}
          >
            <IoArrowDown size={20} /> Ajouter Ligne
          </Button>
          <Button
            className="ml-2"
            color="danger"
            isDisabled={billitSent}
            radius="lg"
            onPress={delLine}
          >
            <IoArrowUp size={20} /> Supprimer Ligne
          </Button>
        </div>
        <div className="basis-1/2 md:basis-1/4 p-2 flex justify-end">
          <PrintButton
            printAction={() => {
              verifyAndSave(true);
            }}
          />
          <SaveButton
            isDisabled={saveDisabled}
            isLoading={isLoadingCnote}
            isSaved={saved}
            saveAction={() => verifyAndSave()}
            tooltipText={saveTooltip}
          />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>
    </>
  );
};

export default CreditNote;
