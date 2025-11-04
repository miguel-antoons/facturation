import { Autocomplete, AutocompleteItem } from "@heroui/autocomplete";
import { useEffect, useState } from "react";
import {addToast} from "@heroui/toast";

const ClientAutocomplete = ({
  setIsLoadingCustomers = (_newVal: boolean) => {},
  setEmailPresent = (_newVal: { [key: string]: boolean }) => {},
  setClientHasVat = (_newVal: { [key: string]: boolean }) => {},
  customerId,
  setCustomerId = (_newVal: string) => {},
}: {
  setIsLoadingCustomers?: (newVal: boolean) => void;
  setEmailPresent?: (newVal: { [key: string]: boolean }) => void;
  setClientHasVat?: (newVal: { [key: string]: boolean }) => void;
  customerId: string | number;
  setCustomerId?: (newVal: string) => void;
}) => {
  const [customers, setCustomers] = useState([]);

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
        // setIsLoadingCnote(false);
      });
  }, []);

  return (
    <Autocomplete
      defaultItems={customers}
      label="Choisissez un Client"
      selectedKey={String(customerId)}
      // @ts-ignore
      onSelectionChange={(event) => setCustomerId(event)}
    >
      {(customer: { key: string; label: string }) => (
        <AutocompleteItem key={customer.key}>
          {customer.label}
        </AutocompleteItem>
      )}
    </Autocomplete>
  );
};

export default ClientAutocomplete;
