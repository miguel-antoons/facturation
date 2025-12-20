// @ts-ignore
import { LinkContainer } from "react-router-bootstrap";
import { Button } from "@heroui/button";
import {
  IoDocumentText,
  IoDocumentTextOutline,
  // IoGrid,
  IoPeople,
} from "react-icons/io5";

const Home = () => {
  return (
    <div className="h-screen bg-gradient-to-br from-pink-500 via-white to-blue-500">
      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/1 md:basis-1/2 p-2">
          <h1 className="text-4xl font-bold text-white sm:truncate sm:text-4xl sm:tracking-tight">
            Bienvenue
          </h1>
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/2 md:basis-1/4 p-2">
          <LinkContainer to="/billlist">
            <Button
              className="text-2xl font-bold bg-linear-to-tr from-pink-500 to-yellow-500 text-white shadow-lg w-full h-full"
              radius="lg"
            >
              <IoDocumentText size={200} />
              Factures
            </Button>
          </LinkContainer>
        </div>
        <div className="basis-1/2 md:basis-1/4 p-2">
          <LinkContainer to="/customerlist">
            <Button
              className="text-2xl font-bold bg-linear-to-tr from-green-400 to-blue-500 text-white shadow-lg w-full h-full"
              radius="lg"
            >
              <IoPeople size={200} />
              Clients
            </Button>
          </LinkContainer>
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/2 md:basis-1/4 p-2">
          <LinkContainer to="/cnotelist">
            <Button
              className="text-2xl font-bold bg-gradient-to-tr from-orange-400 to-sky-400 text-white shadow-lg w-full h-full"
              radius="lg"
            >
              <IoDocumentTextOutline size={200} />
              Notes de Crédit
            </Button>
          </LinkContainer>
        </div>
        <div className="basis-1/2 md:basis-1/4 p-2">
          {/*<LinkContainer to="/tickets/0">*/}
          {/*  <Button*/}
          {/*    className="text-2xl font-bold bg-linear-to-r from-yellow-200 via-lime-400 to-green-600 text-white shadow-lg w-full h-full"*/}
          {/*    radius="lg"*/}
          {/*  >*/}
          {/*    <IoGrid size={200} />*/}
          {/*    Étiquettes*/}
          {/*  </Button>*/}
          {/*</LinkContainer>*/}
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>
    </div>
  );
};

export default Home;
