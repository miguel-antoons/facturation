import { Button } from "@heroui/button";
import { IoGlobe } from "react-icons/io5";
import { useState } from "react";
import { Tooltip } from "@heroui/tooltip";
import { addToast } from "@heroui/toast";

const SendPeppolButton = ({
  orderId,
  orderSaved,
  clientHasVAT,
  isAlreadySent,
  isPending,
  setIsAlreadySent,
}: {
  orderId: number;
  orderSaved: boolean;
  clientHasVAT: boolean;
  isAlreadySent: boolean;
  isPending: boolean;
  setIsAlreadySent: (value: boolean) => void;
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const buttonClicked = isAlreadySent || isPending;
  let tooltipText = "";

  if (!orderSaved) tooltipText = "Veuillez d'abord enregistrer la facture.";
  else if (!clientHasVAT)
    tooltipText =
      "Le client doit avoir un numéro de TVA pour envoyer la facture via Peppol.";
  else if (isAlreadySent)
    tooltipText = "La facture à déjà été envoyée via Peppol.";

  let iconColor = "";

  if (isPending) iconColor = "text-yellow-500";
  else if (isAlreadySent) iconColor = "text-green-500";

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

  return orderSaved && clientHasVAT && !buttonClicked ? (
    <Button
      className="mr-2"
      color="primary"
      isDisabled={false}
      isLoading={isLoading}
      radius="lg"
      startContent={<IoGlobe color={iconColor} size={20} />}
      variant={buttonClicked ? "light" : "solid"}
      onPress={() => sendToPeppol()}
    >
      Peppol
    </Button>
  ) : (
    <Tooltip content={tooltipText} placement="top">
      <div>
        <Button
          className="mr-2"
          color="primary"
          isDisabled={!(orderSaved && clientHasVAT)}
          isLoading={isLoading}
          radius="lg"
          startContent={<IoGlobe color={iconColor} size={20} />}
          variant={buttonClicked ? "light" : "solid"}
          onPress={() => sendToPeppol()}
        >
          Peppol
        </Button>
      </div>
    </Tooltip>
  );
};

export default SendPeppolButton;
