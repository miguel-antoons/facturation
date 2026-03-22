import { Button } from "@heroui/button";
import { IoCloudUpload } from "react-icons/io5";
import { useState } from "react";
import { Tooltip } from "@heroui/tooltip";
import { addToast } from "@heroui/toast";
import {
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  useDisclosure,
} from "@heroui/modal";

const SendBillitButton = ({
  orderId,
  isSent,
  setIsSent,
  isDisabled,
  toolTipText,
  apiRoute,
}: {
  orderId: string;
  orderSaved: boolean;
  isSent: boolean;
  setIsSent: (value: boolean) => void;
  isDisabled: boolean;
  toolTipText: string;
  apiRoute: string;
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const { isOpen, onOpen, onOpenChange } = useDisclosure(); // modal state from heroui

  const iconColor = isSent ? "green" : "";

  const sendToBillit = async () => {
    setIsLoading(true);
    await fetch(`${apiRoute}${orderId}`, {
      method: "POST",
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success || data.status === "success") {
          addToast({
            title: "Facture envoyée",
            description: "La facture a été envoyée avec succès à Billit.",
            color: "success",
          });
          setIsSent(true);
        } else {
          addToast({
            title: "Erreur",
            description:
              "Une erreur est survenue lors de l'envoi de la facture à Billit. Veuillez réessayer plus tard.",
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
            "Une erreur est survenue lors de l'envoi de la facture à Billit. Veuillez réessayer plus tard.",
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
      color="secondary"
      isDisabled={isDisabled}
      isLoading={isLoading}
      radius="lg"
      startContent={
        isLoading ? "" : <IoCloudUpload color={iconColor} size={20} />
      }
      variant={isSent ? "light" : "solid"}
      onPress={() => onOpen()}
    >
      Billit
    </Button>
  );

  return (
    <>
      {toolTipText ? (
        <Tooltip content={toolTipText} placement="top">
          <div>{button}</div>
        </Tooltip>
      ) : (
        button
      )}

      <Modal isOpen={isOpen} onOpenChange={onOpenChange}>
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader className="flex flex-col gap-1">
                Attention!
              </ModalHeader>
              <ModalBody>
                Êtes-vous sûr de vouloir envoyer cette facture à Billit? Une
                fois envoyée, vous ne pourrez plus la modifier. Cette action est
                irréversible.
              </ModalBody>
              <ModalFooter>
                <Button
                  color="default"
                  onPress={() => {
                    onClose();
                  }}
                >
                  Non, Annuler
                </Button>
                <Button
                  color="success"
                  onPress={() => {
                    onClose();
                    sendToBillit();
                  }}
                >
                  Oui, Continuer
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </>
  );
};

export default SendBillitButton;
