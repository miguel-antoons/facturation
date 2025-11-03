import {IoPrint} from "react-icons/io5";
import {Button} from "@heroui/button";

const PrintButton = ({ printAction }: { printAction: () => void }) => {
  return (
    <Button
      className="mr-2"
      radius="lg"
      onPress={printAction}
    >
      <IoPrint size={20} />
      Imprimer
    </Button>
  );
}

export default PrintButton;
