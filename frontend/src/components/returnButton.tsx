import { Button } from "@heroui/button";
import { IoArrowBackCircle } from "react-icons/io5";
// @ts-ignore
import { LinkContainer } from "react-router-bootstrap";

const ReturnButton = ({ to }: { to: string }) => {
  return (
    <LinkContainer to={to}>
      <Button radius="lg">
        <IoArrowBackCircle size={20} />
        Retour
      </Button>
    </LinkContainer>
  );
};

export default ReturnButton;
