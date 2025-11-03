import { CircularProgress } from "@heroui/progress";
import { IoCheckmarkDoneCircle, IoCloseCircle } from "react-icons/io5";

const SaveStatus = ({
  isLoading,
  saved,
}: {
  isLoading: boolean[];
  saved: boolean;
}) => {
  if (isLoading.some((loading) => loading)) {
    return <CircularProgress aria-label="Chargement..." size="md" />;
  }

  return saved ? (
    <>
      <h2 className="font-bold text-gray-900 sm:truncate text-xl sm:tracking-tight">
        Enregistré
      </h2>{" "}
      <IoCheckmarkDoneCircle color="green" size={30} />
    </>
  ) : (
    <>
      <h2 className="font-bold text-gray-900 sm:truncate text-xl sm:tracking-tight">
        Pas Enregistré
      </h2>{" "}
      <IoCloseCircle color="red" size={30} />
    </>
  );
};

export default SaveStatus;
