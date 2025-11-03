import { IoSave } from "react-icons/io5";
import { Button } from "@heroui/button";

const SaveButton = ({
  saveStatus,
  saveAction,
}: {
  saveStatus: boolean;
  saveAction: () => void;
}) => {
  return (
    <Button
      color="success"
      radius="lg"
      variant={saveStatus ? "light" : "solid"}
      onPress={saveAction}
    >
      <IoSave size={20} />
      Enregistrer
    </Button>
  );
};

export default SaveButton;
