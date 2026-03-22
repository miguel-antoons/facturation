import { Button } from "@heroui/button";
import { IoGlobe } from "react-icons/io5";
import { useState } from "react";
import { Tooltip } from "@heroui/tooltip";
import { addToast } from "@heroui/toast";

import { isSentToPeppol, PeppolStatus } from "@/utils/peppol.ts";

const SendPeppolButton = ({
  apiRoute,
  orderId,
  isDisabled,
  peppolStatus,
  setPeppolStatus,
  tooltipText,
}: {
  apiRoute: string;
  orderId: string;
  isDisabled: boolean;
  peppolStatus: number;
  setPeppolStatus: (value: number) => void;
  tooltipText?: string;
}) => {
  const statusToColor = {
    [PeppolStatus.NOT_SENT]: "",
    [PeppolStatus.UNKNOWN]: "",
    [PeppolStatus.PENDING]: "orange",
    [PeppolStatus.RECEIVED]: "green",
  };
  const [isLoading, setIsLoading] = useState(false);
  const buttonClicked = isSentToPeppol(peppolStatus);

  const sendToPeppol = async () => {
    setIsLoading(true);
    await fetch(`${apiRoute}${orderId}`, {
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
          setPeppolStatus(PeppolStatus.PENDING);
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
      })
      .finally(() => {
        setIsLoading(false);
      });
  };

  const button = (
    <Button
      className="mr-2"
      color="primary"
      isDisabled={isDisabled}
      isLoading={isLoading}
      radius="lg"
      startContent={
        isLoading ? (
          ""
        ) : (
          <IoGlobe color={statusToColor[peppolStatus]} size={20} />
        )
      }
      variant={buttonClicked ? "light" : "solid"}
      onPress={() => sendToPeppol()}
    >
      Peppol
    </Button>
  );

  return tooltipText ? (
    <Tooltip content={tooltipText} placement="top">
      <div>{button}</div>
    </Tooltip>
  ) : (
    button
  );
};

export default SendPeppolButton;
