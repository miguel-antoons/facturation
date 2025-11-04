import {
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
} from "@heroui/modal";
import { Button } from "@heroui/button";
import { ReactElement } from "react";

const FormConfirmModal = ({
  isOpen,
  onOpenChange,
  modalText,
  setModalText,
  setPrinting = (_newVal: boolean) => {},
  printing = false,
  saveChanges = (_newVal: boolean) => {},
}: {
  isOpen: boolean;
  onOpenChange: () => void;
  modalText: ReactElement;
  setModalText: (newVal: ReactElement) => void;
  setPrinting?: (newVal: boolean) => void;
  printing?: boolean;
  saveChanges?: (proceedWithPrint: boolean) => void;
}) => {
  return (
    <Modal isOpen={isOpen} onOpenChange={onOpenChange}>
      <ModalContent>
        {(onClose) => (
          <>
            <ModalHeader className="flex flex-col gap-1">
              Attention!
            </ModalHeader>
            <ModalBody>{modalText}</ModalBody>
            <ModalFooter>
              <Button
                color="default"
                onPress={() => {
                  onClose();
                  setPrinting(false);
                  setModalText(<></>);
                }}
              >
                Non, Annuler
              </Button>
              {printing ? (
                <Button
                  color="success"
                  onPress={() => {
                    onClose();
                    setPrinting(false);
                    setModalText(<></>);
                    saveChanges(true);
                  }}
                >
                  Oui, Continuer
                </Button>
              ) : (
                <Button
                  color="success"
                  onPress={() => {
                    onClose();
                    setModalText(<></>);
                    saveChanges(false);
                  }}
                >
                  Oui, Continuer
                </Button>
              )}
            </ModalFooter>
          </>
        )}
      </ModalContent>
    </Modal>
  );
};

export default FormConfirmModal;
