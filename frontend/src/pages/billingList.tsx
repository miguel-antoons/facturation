import { addToast } from "@heroui/toast";

import ProjectPage from "@/components/projectPage";

const BillingList = () => {
  const fetchContent = async () => {
    const formattedData: {
      id: number;
      number: number;
      attribute1: string;
      attribute2: string;
      attribute3: string;
      fileId: string | null;
    }[] = [];

    try {
      const response = await fetch("/api/bills");
      const dataJson = await response.json();
      const data: {
        OrderID: string;
        OrderNumber: string;
        CounterParty: { DisplayName: string };
        OrderTitle: string;
        OrderDate: string;
      }[] = dataJson.Items;

      data.forEach(
        (element: {
          OrderID: string;
          OrderNumber: string;
          CounterParty: { DisplayName: string };
          OrderTitle: string;
          OrderDate: string;
        }) => {
          let attr3: string | Date = element.OrderDate
            ? new Date(element.OrderDate)
            : "N/A";
          const dateOptions = {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
          };

          if (attr3 !== "N/A") {
            // @ts-ignore
            attr3 = attr3.toLocaleString("fr-BE", dateOptions);
          }
          formattedData.push({
            id: Number(element.OrderID),
            number: Number(element.OrderNumber),
            fileId: element.OrderID,
            attribute1: element.CounterParty.DisplayName
              ? element.CounterParty.DisplayName
              : "N/A",
            attribute2: element.OrderTitle ? element.OrderTitle : "N/A",
            attribute3: attr3,
          });
        },
      );
    } catch (e) {
      addToast({
        title: "Erreur",
        description:
          "Impossible de retrouver la liste de factures. Veuillez réessayer plus tard.",
        color: "danger",
      });
      // eslint-disable-next-line
      console.log(e);
    }

    return formattedData;
  };

  return (
    <ProjectPage
      apiPathname="/bills"
      attribute1="Client"
      attribute2="Chantier"
      attribute3="Date de Création"
      attribute3SearchFun={(attr3, searchTerm) =>
        attr3.split("/")[2] === searchTerm ||
        (searchTerm.indexOf("/") > -1 && attr3.indexOf(searchTerm) > -1)
      }
      fadeClass="bg-linear-to-tr from-pink-500 to-yellow-500"
      fetchContent={fetchContent}
      instancePath="/bill"
      title="Bienvenue dans Factures"
    />
  );
};

export default BillingList;
