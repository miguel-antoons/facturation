import { addToast } from "@heroui/toast";

import ProjectPage from "@/components/projectPage";

const CustomerList = () => {
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
      const response = await fetch("/api/customers");
      const data = await response.json();

      data.forEach(
        (element: {
          id: number;
          city: string;
          company: string;
          name: string;
          phones: string[];
          postal_code: string;
          surname: string;
        }) => {
          if (
            element.id === 0 ||
            element.id === undefined ||
            element.id === null
          )
            return;
          let attribute1: string;

          if (element.name === null && element.surname === null) {
            attribute1 = element.company === null ? "N/A" : element.company;
          } else if (element.company === null) {
            attribute1 = `${element.name === null ? "" : element.name} ${element.surname === null ? "" : element.surname}`;
          } else {
            attribute1 = `${element.name === null ? "" : element.name} ${element.surname === null ? "" : element.surname}, ${element.company}`;
          }
          formattedData.push({
            id: Number(element.id),
            number: Number(element.id),
            attribute1: attribute1,
            attribute2: element.phones.length > 0 ? element.phones[0] : "N/A",
            attribute3: `${element.postal_code}, ${element.city}`,
            fileId: String(element.id),
          });
        },
      );
    } catch (e) {
      addToast({
        title: "Erreur",
        description:
          "Impossible de retrouver la liste de clients. Veuillez réessayer plus tard.",
        color: "danger",
      });
      // eslint-disable-next-line
      console.log(e);
    }

    return formattedData;
  };

  return (
    <ProjectPage
      apiPathname="/customers"
      attribute1="Nom, Prénom, Société"
      attribute2="N° de Téléphone"
      attribute3="Ville"
      fadeClass="from-green-400 to-blue-500"
      fetchContent={fetchContent}
      instancePath="/customer"
      title="Bienvenue dans Clients"
    />
  );
};

export default CustomerList;
