import { addToast } from "@heroui/toast";
import { IoDocumentTextOutline } from "react-icons/io5";
import { useNavigate } from "react-router-dom";

import ProjectPage from "@/components/projectPage";

const BillingList = () => {
  const navigate = useNavigate();

  const fetchContent = async () => {
    const formattedData: {
      id: string;
      number: string;
      attribute1: string;
      attribute2: string;
      attribute3: string;
    }[] = [];

    try {
      const response = await fetch("/api/bills");
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

  const goToCnote = (billId: string) => {
    fetch(`/api/bills/${billId}`)
      .then((res) => res.json())
      .then((data) => {
        const link = `/cnote/0?bill=${data.orderNumber}&customerId=${data.customerId}&title=${data.orderTitle}&ventilationCode=${data.ventilationCode}`;

        navigate(link);
      })
      .catch((error) => {
        addToast({
          title: "Erreur",
          description: `Impossible de créer une note de crédit à partir de cette facture. Veuillez réessayer plus tard.`,
          color: "danger",
        });
        // eslint-disable-next-line
        console.log(error);
      });
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
      customButtonAction={goToCnote}
      customButtonText={
        <>
          <IoDocumentTextOutline size={20} /> Cnote
        </>
      }
      fadeClass="bg-linear-to-tr from-pink-500 to-yellow-500"
      fetchContent={fetchContent}
      instancePath="/bill"
      title="Bienvenue dans Factures"
    />
  );
};

export default BillingList;
