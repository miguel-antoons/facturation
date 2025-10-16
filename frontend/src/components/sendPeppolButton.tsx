import { Button } from "@heroui/button";
import { IoGlobe } from "react-icons/io5";
import { useState } from "react";
import { Tooltip } from "@heroui/tooltip";
import { addToast } from "@heroui/toast";

const SendPeppolButton = ({
  orderId,
  billSaved,
  clientHasVAT,
  isAlreadySent,
  setIsAlreadySent,
}: {
  orderId: number;
  billSaved: boolean;
  clientHasVAT: boolean;
  isAlreadySent: boolean;
  setIsAlreadySent: (value: boolean) => void;
}) => {
  const [isLoading, setIsLoading] = useState(false);
  let tooltipText = "";

  if (!billSaved) tooltipText = "Veuillez d'abord sauvegarder la facture.";
  else if (!clientHasVAT)
    tooltipText =
      "Le client doit avoir un numéro de TVA pour envoyer la facture via Peppol.";
  else if (isAlreadySent)
    tooltipText = "La facture à déjà été envoyée via Peppol.";

  const sendToPeppol = async () => {
    setIsLoading(true);
    await fetch(`/api/bills//sendPeppol/${orderId}`, {
      method: "POST",
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success || data.status === "success") {
          addToast({
            title: "Facture envoyée",
            description: "La facture a été envoyée avec succès via Peppol.",
            color: "success",
          });
          setIsAlreadySent(true);
        } else {
          addToast({
            title: "Erreur",
            description:
              "Une erreur est survenue lors de l'envoi de la facture via Peppol. Veuillez réessayer plus tard.",
            color: "danger",
          });
          // eslint-disable-next-line
          console.log(data);
        }
      })
      .catch((error) => {
        addToast({
          title: "Erreur",
          description:
            "Une erreur est survenue lors de l'envoi de la facture via Peppol. Veuillez réessayer plus tard.",
          color: "danger",
        });
        // eslint-disable-next-line
        console.log(error);
      });
    setIsLoading(false);
  };

  return billSaved && clientHasVAT ? (
    <Tooltip content={tooltipText} placement="top">
      <Button
        className="mr-2"
        color="primary"
        isDisabled={false}
        isLoading={isLoading}
        radius="lg"
        startContent={<IoGlobe size={20} />}
        variant={isAlreadySent ? "light" : "solid"}
        onPress={() => sendToPeppol()}
      >
        Peppol
      </Button>
    </Tooltip>
  ) : (
    <Tooltip content={tooltipText} placement="top">
      <div>
        <Button
          className="mr-2"
          color="primary"
          isDisabled={true}
          isLoading={isLoading}
          radius="lg"
          startContent={<IoGlobe size={20} />}
        >
          Peppol
        </Button>
      </div>
    </Tooltip>
  );
};

export default SendPeppolButton;
