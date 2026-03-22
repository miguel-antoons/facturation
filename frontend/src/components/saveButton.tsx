import { IoSave } from "react-icons/io5";
import { Button } from "@heroui/button";
import { Tooltip } from "@heroui/tooltip";

const SaveButton = ({
  isDisabled = false,
  isSaved,
  saveAction,
  tooltipText = "",
  isLoading = false,
}: {
  isDisabled?: boolean;
  isSaved: boolean;
  saveAction: () => void;
  tooltipText?: string;
  isLoading?: boolean;
}) => {
  const button = (
    <Button
      color="success"
      isDisabled={isDisabled}
      isLoading={isLoading}
      radius="lg"
      startContent={isLoading ? "" : <IoSave size={20} />}
      variant={isSaved ? "light" : "solid"}
      onPress={saveAction}
    >
      Enregistrer
    </Button>
  );

  return tooltipText ? (
    <Tooltip content={tooltipText}>
      <div>{button}</div>
    </Tooltip>
  ) : (
    button
  );
};

export default SaveButton;
