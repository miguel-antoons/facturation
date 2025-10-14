// @ts-ignore
import { LinkContainer } from "react-router-bootstrap";
import { Button } from "@heroui/button";
import { IoDocuments, IoPeople } from "react-icons/io5";

const Home = () => {
  return (
    <>
      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/1 md:basis-1/2 p-2">
          <h1 className="text-4xl font-bold text-gray-900 sm:truncate sm:text-4xl sm:tracking-tight">
            Bienvenue
          </h1>
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>
      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/2 md:basis-1/4 p-2">
          <LinkContainer to="/billlist">
            <Button className="text-2xl font-bold bg-linear-to-tr from-pink-500 to-yellow-500 text-white shadow-lg w-1/1 h-auto">
              <IoDocuments size={200} />
              Factures
            </Button>
          </LinkContainer>
        </div>
        <div className="basis-1/2 md:basis-1/4 p-2">
          <LinkContainer to="/customerlist">
            <Button className="text-2xl font-bold bg-linear-to-tr from-green-400 to-blue-500 text-white shadow-lg w-1/1 h-auto">
              <IoPeople size={200} />
              Clients
            </Button>
          </LinkContainer>
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>
    </>
  );
};

export default Home;
