import { addToast } from "@heroui/toast";

import ProjectPage from "@/components/projectPage";

const CreditNoteList = () => {
  const fetchContent = async () => {
    const formattedData: {
      id: string;
      number: string;
      attribute1: string;
      attribute2: string;
      attribute3: string;
    }[] = [];

    try {
      const response = await fetch("/api/cnotes");
      const data: {
        orderId: string;
        orderNumber: string;
        customerName: string;
        orderTitle: string;
        orderDate: string;
      }[] = await response.json();

      data.forEach(
        (element: {
          orderId: string;
          orderNumber: string;
          customerName: string;
          orderTitle: string;
          orderDate: string;
        }) => {
          let attr3: string | Date = element.orderDate
            ? new Date(element.orderDate)
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
            id: element.orderId,
            number: element.orderNumber,
            attribute1: element.customerName ? element.customerName : "N/A",
            attribute2: element.orderTitle ? element.orderTitle : "N/A",
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
      apiPathname="/cnotes"
      attribute1="Client"
      attribute2="Objet"
      attribute3="Date de Création"
      attribute3SearchFun={(attr3, searchTerm) =>
        attr3.split("/")[2] === searchTerm ||
        (searchTerm.indexOf("/") > -1 && attr3.indexOf(searchTerm) > -1)
      }
      fadeClass="bg-gradient-to-tr from-orange-400 to-sky-400"
      fetchContent={fetchContent}
      instancePath="/cnote"
      title="Bienvenue dans Notes de Crédit"
    />
  );
};

export default CreditNoteList;
