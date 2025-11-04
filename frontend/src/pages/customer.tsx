import { Input, Textarea } from "@heroui/input";
import { useState, useEffect } from "react";
import { Select, SelectItem } from "@heroui/select";
import { addToast } from "@heroui/toast";
import { useDisclosure } from "@heroui/modal";
import { useNavigate, useParams } from "react-router-dom";

import SaveStatus from "@/components/saveStatus.tsx";
import ReturnButton from "@/components/returnButton.tsx";
import PrintButton from "@/components/printButton.tsx";
import SaveButton from "@/components/saveButton.tsx";
import FormConfirmModal from "@/components/formConfirmModal.tsx";

const Customer = () => {
  // language options for select
  // key is used for react key, value for the value sent to the backend, label for display
  // first option is default
  // when adding a language, also update reverseLanguageOptions
  // and the languageOptions in src/pages/billing.tsx
  const languageOptions = [
    { value: "fr", label: "Français", key: "fr" },
    { value: "nl", label: "Néerlandais", key: "nl" },
  ];
  let customerId = Number(useParams().id); // get customer id from url
  const [heading, setHeading] = useState(""); // heading of the page
  const [lastName, setLastName] = useState(""); // last name of the customer
  const [surname, setSurname] = useState(""); // surname of the customer
  const [company, setCompany] = useState(""); // company of the customer
  const [street, setStreet] = useState(""); // street of the customer
  const [number, setNumber] = useState(""); // number of the customer
  const [postalCode, setPostalCode] = useState(""); // postal code of the customer
  const [city, setCity] = useState(""); // city of the customer
  const [vatNumber, setVatNumber] = useState(""); // vat number of the customer
  const [language, setLanguage] = useState(""); // language of the customer, default to first option
  const [architectName, setArchitectName] = useState(""); // architect name of the customer
  const [comment, setComment] = useState(""); // comment of the customer
  const [isLoading, setIsLoading] = useState(false); // loading state of the page
  const [saved, setSaved] = useState(false); // save icon state of the page
  const [lastSave, setLastSave] = useState({}); // last saved state of the page
  const [modalText, setModalText] = useState(<></>); // text to display in the modal
  const [printing, setPrinting] = useState(false); // printing state of the page
  const navigate = useNavigate(); // navigate function from react router
  const { isOpen, onOpen, onOpenChange } = useDisclosure(); // modal state from heroui

  useEffect(() => {
    // fetch customer data from backend if customerId is not 0 (new customer)
    if (customerId !== 0 && customerId !== undefined) {
      setIsLoading(true);
      fetch(`/api/customers/${customerId}`)
        .then((response) => response.json())
        .then(
          (data: {
            name: string;
            surname: string;
            company: string;
            street: string;
            number: string;
            postal_code: string;
            city: string;
            vat_number: string;
            language: string;
            architect_name: string;
            comment: string;
          }) => {
            setLastName(data.name ?? "");
            setSurname(data.surname ?? "");
            setCompany(data.company ?? "");
            setStreet(data.street ?? "");
            setNumber(data.number ?? "");
            setPostalCode(data.postal_code ?? "");
            setCity(data.city ?? "");
            setVatNumber(data.vat_number ?? "");
            setLanguage(data.language ?? "");
            setArchitectName(data.architect_name ?? "");
            setComment(data.comment ?? "");
            setSaved(true);
            setIsLoading(false);
            setLastSave({
              name: data.name ?? "",
              surname: data.surname ?? "",
              company: data.company ?? "",
              street: data.street ?? "",
              number: data.number ?? "",
              postal_code: data.postal_code ?? "",
              city: data.city ?? "",
              vat_number: data.vat_number ?? "",
              language: data.language ?? "",
              architect_name: data.architect_name ?? "",
              comment: data.comment ?? "",
            });
          },
        )
        .catch((error) => {
          addToast({
            title: "Erreur",
            description: `Impossible de charger le client avec l'ID ${customerId}. Veuillez réessayer plus tard.`,
            color: "danger",
          });
          // eslint-disable-next-line
          console.log(error);
        });
    }
  }, []);

  useEffect(() => {
    // set heading based on customerId
    if (customerId === 0 || customerId === undefined) {
      setHeading("Nouveau Client");
    } else {
      setHeading(`Client Numéro ${customerId}`);
    }
  }, [customerId]);

  /**
   * Check if the current state is different from the last saved state
   * @returns true if different, false if same
   */
  const isDifferentFromLastSave = () => {
    return (
      JSON.stringify({
        name: lastName,
        surname: surname,
        company: company,
        street: street,
        number: number,
        postal_code: postalCode,
        city: city,
        vat_number: vatNumber,
        language: language,
        architect_name: architectName,
        comment: comment,
      }) !== JSON.stringify(lastSave)
    );
  };

  const verifyAndSave = (printMe = false) => {
    // function to verify the data before saving
    setModalText(<></>);
    if (lastName === "" && surname === "" && company === "") {
      // at least one of lastName, surname or company must be filled
      addToast({
        title: "Erreur",
        description: "Veuillez entrer au moins un nom, prénom ou une société.",
        color: "danger",
      });

      return;
    }

    const incompleteAddress =
      street === "" || number === "" || postalCode === "" || city === ""; // address must be complete
    const missingVat = company !== "" && vatNumber === ""; // if company is filled, vat number must be filled
    const missingEmail = noMailPresent(comment); // email must be present in comment

    // create modal text based on missing fields
    const modalText = (
      <>
        {incompleteAddress ? <p>L&lsquo;adresse est incomplète.</p> : null}
        {missingVat ? <p>Le numéro de TVA est manquant.</p> : null}
        {missingEmail ? (
          <p>Aucun email n&lsquo;a été trouvé dans le commentaire.</p>
        ) : null}
        <p>
          <b>Êtes vous sur de vouloir continuer?</b>
        </p>
      </>
    );

    if (incompleteAddress || missingVat || missingEmail) {
      setPrinting(printMe);
      // if any of the above conditions are true, show modal
      setModalText(modalText);
      onOpen();

      return;
    }

    saveChanges(printMe);
  };

  const saveChanges = (printMe = false) => {
    const differentFromLastSave = isDifferentFromLastSave();

    if (!differentFromLastSave) setSaved(true);
    // if already loading, do nothing (prevents double click)
    if ((isLoading || !differentFromLastSave) && printMe)
      printElement(customerId);
    if (isLoading || !differentFromLastSave) return;

    setIsLoading(true);

    const customerData = {
      name: lastName,
      surname: surname,
      company: company,
      street: street,
      number: number,
      postal_code: postalCode,
      city: city,
      vat_number: vatNumber,
      architect_name: architectName,
      language: language,
      comment: comment,
    };

    // define behavior on success
    const onSuccess = (id: number) => {
      if (printMe) printElement(id);
      if (customerId === 0 || customerId === undefined) {
        // if new customer, navigate to the new customer's page
        navigate(`/customer/${id}`);
      }
      setSaved(true);
      setIsLoading(false);
      setLastSave({
        name: lastName,
        surname: surname,
        company: company,
        street: street,
        number: number,
        postal_code: postalCode,
        city: city,
        vat_number: vatNumber,
        language: language,
        architect_name: architectName,
        comment: comment,
      });
      addToast({
        title: "Client Enregistré",
        description: `Le client numéro ${id} a été enregistré avec succès.`,
        color: "success",
      });
    };

    // define behavior on failure
    const onFailure = (error: any) => {
      setIsLoading(false);
      addToast({
        title: "Erreur",
        description:
          "Impossible d'enregistrer' le client. Veuillez réessayer plus tard.",
        color: "danger",
      });
      // eslint-disable-next-line
      console.log(error);
    };

    if (customerId === 0 || customerId === undefined) {
      // Create new customer
      fetch("/api/customers", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(customerData),
      })
        .then((response) => response.json())
        .then((data: { id: number }) => onSuccess(data.id))
        .catch((error) => onFailure(error));
    } else {
      // Update existing customer
      fetch(`/api/customers/${customerId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(customerData),
      })
        .then((response) => response.json())
        .then(() => onSuccess(customerId))
        .catch((error) => onFailure(error));
    }
  };

  const noMailPresent = (text: string): boolean => {
    // regex to find email in text
    const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/;

    return !emailRegex.test(text);
  };

  const change = (fun: (val: any) => void, value: any) => {
    fun(value);
    setSaved(false);
  };

  const printElement = async (id: number) => {
    const response = await fetch(`/api/files/customers/${id}`, {
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
          <SaveStatus isLoading={[isLoading]} saved={saved} />
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
        <div className="basis-1/3 md:basis-1/6 p-2">
          <ReturnButton to="/customerlist" />
        </div>
        <div className="basis-2/3 md:basis-2/6 p-2 flex justify-end">
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
          <Input
            label="Nom"
            type="text"
            value={lastName}
            onChange={(e) => change(setLastName, e.target.value)}
          />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/1 md:basis-4/8 p-2">
          <Input
            label="Prénom"
            type="text"
            value={surname}
            onChange={(e) => change(setSurname, e.target.value)}
          />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/1 md:basis-4/8 p-2">
          <Input
            label="Société"
            type="text"
            value={company}
            onChange={(e) => change(setCompany, e.target.value)}
          />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-4/5 md:basis-2/5 p-2">
          <Input
            label="Rue"
            type="text"
            value={street}
            onChange={(e) => change(setStreet, e.target.value)}
          />
        </div>
        <div className="basis-1/5 md:basis-1/10 p-2">
          <Input
            label="Numéro"
            type="text"
            value={number}
            onChange={(e) => change(setNumber, e.target.value)}
          />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/3 md:basis-1/6 p-2">
          <Input
            label="Code Postal"
            type="text"
            value={postalCode}
            onChange={(e) => change(setPostalCode, e.target.value)}
          />
        </div>
        <div className="basis-2/3 md:basis-2/6 p-2">
          <Input
            label="Ville"
            type="text"
            value={city}
            onChange={(e) => change(setCity, e.target.value)}
          />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/1 md:basis-4/8 p-2">
          <Input
            label="Numéro de TVA"
            type="text"
            value={vatNumber}
            onChange={(e) => change(setVatNumber, e.target.value)}
          />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/1 md:basis-4/8 p-2">
          <Input
            label="Nom d'Architecte"
            type="text"
            value={architectName}
            onChange={(e) => change(setArchitectName, e.target.value)}
          />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/1 md:basis-4/8 p-2">
          <Select
            // @ts-ignore
            classNames="max-w-xs"
            label="Langue"
            selectedKeys={[language]}
            onChange={(event) => change(setLanguage, event.target.value)}
          >
            {languageOptions.map((option) => (
              // @ts-ignore
              <SelectItem key={option.key} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </Select>
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/1 md:basis-4/8 p-2">
          <Textarea
            label="Commentaire, Email"
            minRows={2}
            placeholder="Entrez une Description"
            value={comment}
            onChange={(e) => change(setComment, e.target.value)}
          />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/1 md:basis-1/2 p-2 flex justify-end">
          <SaveButton saveAction={() => verifyAndSave()} saveStatus={saved} />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>
    </>
  );
};

export default Customer;
