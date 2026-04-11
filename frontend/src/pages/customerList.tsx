import { addToast } from "@heroui/toast";

import ProjectPage from "@/components/projectPage";

const CustomerList = () => {
  const fetchContent = async () => {
    const formattedData: {
      id: string;
      number: string;
      attribute1: string;
      attribute2: string;
      attribute3: string;
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
          mobileNumbers: string[];
          telephoneNumbers: string[];
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
          const phones = element.mobileNumbers.concat(element.telephoneNumbers);

          formattedData.push({
            id: String(element.id),
            number: String(element.id),
            attribute1: attribute1,
            attribute2: phones.length > 0 ? phones[0] : "N/A",
            attribute3: `${element.postal_code}, ${element.city}`,
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
      attribute2SearchFun={(attr2, searchTerm) => attr2.startsWith(searchTerm)}
      attribute3="Ville"
      attribute3SearchFun={(attr3, searchTerm) =>
        attr3.split(",")[0].startsWith(searchTerm) ||
        attr3.split(",")[1].indexOf(searchTerm) > -1
      }
      fadeClass="bg-linear-to-tr from-green-400 to-blue-500"
      fetchContent={fetchContent}
      instancePath="/customer"
      title="Bienvenue dans Clients"
    />
  );
};

export default CustomerList;
