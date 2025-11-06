import { Button } from "@heroui/button";
import { IoArrowBackCircle } from "react-icons/io5";
import { useNavigate } from "react-router-dom";

const ReturnButton = () => {
  const navigate = useNavigate();

  return (
    <Button radius="lg" onPress={() => navigate(-1)}>
      <IoArrowBackCircle size={20} />
      Retour
    </Button>
  );
};

export default ReturnButton;
