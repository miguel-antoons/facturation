import { useState, useEffect, useRef } from "react";
// eslint-disable-next-line import/order
import * as icon from "react-icons/io5";

import "@/styles/projectTable.css";
// @ts-ignore
import { LinkContainer } from "react-router-bootstrap";
import { Input } from "@heroui/input";
import { Select, SelectItem } from "@heroui/select";
import { Button } from "@heroui/button";
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  useDisclosure,
} from "@heroui/modal";
import { addToast } from "@heroui/toast";
import { IoArrowBackCircle } from "react-icons/io5";

import SearchIcon from "@/components/searchIcon";
import ProjectTable from "@/components/projectTable";

const ProjectPage = ({
  attribute1,
  attribute2,
  attribute3,
  attribute1SearchFun = (attr1, searchTerm) => attr1.indexOf(searchTerm) > -1,
  attribute2SearchFun = (attr2, searchTerm) => attr2.indexOf(searchTerm) > -1,
  attribute3SearchFun = (attr3, searchTerm) => attr3.indexOf(searchTerm) > -1,
  apiPathname,
  title,
  instancePath,
  fadeClass,
  fetchContent,
}: {
  attribute1: string;
  attribute2: string;
  attribute3: string;
  attribute1SearchFun?: (attr1: string, searchTerm: string) => boolean;
  attribute2SearchFun?: (attr2: string, searchTerm: string) => boolean;
  attribute3SearchFun?: (attr3: string, searchTerm: string) => boolean;
  apiPathname: string;
  title: string;
  instancePath: string;
  fadeClass: string;
  fetchContent?: () => Promise<any>;
}) => {
  const [sort, setSort] = useState('{"key": "number", "sign": 1}');
  const [search, setSearch] = useState("");
  const [shownContent, setShownContent] = useState([]);
  const [content, setContent] = useState([]);
  const [tableHeight, setTableHeight] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [idToDelete, setIdToDelete] = useState(0);
  const [numberToDelete, setNumberToDelete] = useState(0);
  const [nameToDelete, setNameToDelete] = useState("");
  const { isOpen, onOpen, onOpenChange } = useDisclosure();
  const ref = useRef(null);
  let previousHeight = window.innerHeight;

  const sortOptions = [
    {
      value: '{"key": "number", "sign": 0}',
      label: `A-Z  #`,
    },
    {
      value: '{"key": "number", "sign": 1}',
      label: `Z-A  #`,
    },
    {
      value: '{"key": "attribute3", "sign": 0}',
      label: `A-Z ${attribute3}`,
    },
    {
      value: '{"key": "attribute3", "sign": 1}',
      label: `Z-A ${attribute3}`,
    },
    {
      value: '{"key": "attribute1", "sign": 0}',
      label: `A-Z ${attribute1}`,
    },
    {
      value: '{"key": "attribute1", "sign": 1}',
      label: `Z-A ${attribute1}`,
    },
    {
      value: '{"key": "attribute2", "sign": 0}',
      label: `A-Z ${attribute2}`,
    },
    {
      value: '{"key": "attribute2", "sign": 1}',
      label: `Z-A ${attribute2}`,
    },
  ];

  useEffect(() => {
    const temp = () =>
      // @ts-ignore
      setTableHeight(window.innerHeight - ref.current.clientHeight);

    window.addEventListener("heightChange", temp);
    window.addEventListener(
      "resize",
      () => {
        if (window.innerHeight > previousHeight) {
          // bigger
          window.dispatchEvent(
            new CustomEvent("heightChange", {
              detail: {
                type: "larger",
                previousHeight,
                newHeight: window.innerHeight,
              },
            }),
          );
        } else if (window.innerHeight < previousHeight) {
          // smaller
          window.dispatchEvent(
            new CustomEvent("heightChange", {
              detail: {
                type: "smaller",
                previousHeight,
                newHeight: window.innerHeight,
              },
            }),
          );
        } else {
          // height not changed
        }
        previousHeight = window.innerHeight;
      },
      { capture: true, passive: false },
    );
    temp();
  }, []);

  // GET information about all content, fires on page load and on filter change
  useEffect(() => {
    setIsLoading(true);
    // @ts-ignore
    fetchContent().then((data) => {
      setContent(data);
      setIsLoading(false);
    });
  }, []);

  const openDeleteModal = (id: number, number: number, name: string) => {
    setNameToDelete(`${number}, ${name}`);
    setIdToDelete(id);
    setNumberToDelete(number);
    onOpen();
  };

  const deleteElement = async () => {
    const id = idToDelete;
    const number = numberToDelete;

    setNameToDelete("");
    setIdToDelete(0);
    setNumberToDelete(0);
    const res = await fetch(`/api${apiPathname}/${id}`, {
      method: "DELETE",
    });
    const data = await res.json();

    if (res.status !== 200 || data.status !== "deleted") {
      addToast({
        title: "Erreur lors de la supression",
        description: `Le serveur a répondu avec le code ${res.status}. Veuillez réessayer plus tard.`,
        color: "danger",
      });

      return;
    }
    addToast({
      title: "Supression réussie",
      description: `La supression de l'élément avec le numéro ${number} a été effectuée avec succès.`,
      color: "success",
    });
    let filteredContent = content.slice();

    filteredContent = filteredContent.filter(
      (element: {
        id: number;
        number: number;
        attribute1: string;
        attribute2: string;
        attribute3: string;
        fileId: string | null;
      }) => element.id !== id,
    );
    setContent(filteredContent);
    sortContent(filteredContent);
  };

  const printElement = async (id: number | string | null) => {
    const response = await fetch(`/api/files${apiPathname}/${id}`, {
      method: "GET",
    });

    // print pdf
    const blob = await response.blob();
    const fileURL = URL.createObjectURL(blob);
    // print in new tab
    const w = window.open(fileURL);

    if (!w) {
      addToast({
        title: "Erreur lors de l'Impression",
        description:
          "Impossible d'ouvrir une nouvelle fenêtre pour l'impression.",
        color: "danger",
      });

      return;
    }
    w.print();
  };

  /**
   * Function sorts the array with all the element according to the users
   * choice and afterward calls a function to filter the sorted result according
   * to the user's choice (again).
   * @param {Array} arrayToSort array to sort and filter
   */
  const sortContent = (
    arrayToSort: {
      id: number;
      number: number;
      attribute1: string;
      attribute2: string;
      attribute3: string;
      fileId: string | null;
    }[],
  ) => {
    let selectedSort: {
      key: "number" | "attribute1" | "attribute2" | "attribute3";
      sign: 0 | 1;
    } = JSON.parse(sort); // get values from html element
    let sortedContent = arrayToSort.slice(); // Create new array from the state array

    sortedContent.sort((a, b) => b.number - a.number); // sort according to the project number

    sortedContent.sort((a, b) => {
      let prime_a;
      let prime_b;
      const dateRegex = /^\d{2}\/\d{2}\/\d{4}$/;

      if (selectedSort["key"] === "number") {
        prime_a = Number(a[selectedSort["key"]]);
        prime_b = Number(b[selectedSort["key"]]);
      } else if (
        dateRegex.test(String(a[selectedSort["key"]])) &&
        dateRegex.test(String(b[selectedSort["key"]]))
      ) {
        // convert dates to iso format for correct comparison
        const [day_a, month_a, year_a] = String(a[selectedSort["key"]]).split(
          "/",
        );
        const [day_b, month_b, year_b] = String(b[selectedSort["key"]]).split(
          "/",
        );

        prime_a = new Date(`${year_a}-${month_a}-${day_a}`);
        prime_b = new Date(`${year_b}-${month_b}-${day_b}`);
      } else {
        prime_a = String(a[selectedSort["key"]]).toLowerCase();
        prime_b = String(b[selectedSort["key"]]).toLowerCase();
      }

      // compares the 2 values and returns the result
      if (prime_a > prime_b) {
        return selectedSort["sign"] ? -1 : 1;
      } else if (prime_b > prime_a) {
        return selectedSort["sign"] ? 1 : -1;
      }

      return 0;
    });

    // @ts-ignore
    setShownContent(filterContent(sortedContent)); // change the (filtered) content order in the actual state
  };

  /**
   * Function fires when the sort option changes or when the user is searching an element.
   * The function will sort the content according to the value chosen by the user
   * and will afterward filter the content according to the value entered the search bar
   * (value is stored in 'search' variable)
   */
  useEffect(() => {
    try {
      sortContent(content);
    } catch (e) {
      // eslint-disable-next-line
      console.log(e);
    }
  }, [sort, search, content]);

  /**
   * function filters an array depending on what is written in the
   * search bar. The content written in the search bar is memorized
   * in the 'search' state variable.
   *
   * @param {Array} unfilteredArray
   * @returns filtered array
   */
  const filterContent = (
    unfilteredArray: {
      id: number;
      number: number;
      attribute1: string;
      attribute2: string;
      attribute3: string;
      fileId: string | null;
    }[],
  ): {
    id: number;
    number: number;
    attribute1: string;
    attribute2: string;
    attribute3: string;
    fileId: string | null;
  }[] => {
    return unfilteredArray.filter((element) => {
      return (
        String(element["number"]).toLowerCase().startsWith(search) ||
        attribute1SearchFun(element["attribute1"], search) ||
        attribute2SearchFun(element["attribute2"], search) ||
        attribute3SearchFun(element["attribute3"], search)
      );
    });
  };

  return (
    <div style={{ margin: 0, padding: 0 }}>
      <div ref={ref} className={`bg-linear-to-tr ${fadeClass} jumbotron`}>
        <div className="d-flex justify-content-center flex flex-row">
          <div className="basis-3/16">
            <LinkContainer to="/">
              <Button
                className="text-white"
                radius="full"
                size="lg"
                variant="light"
              >
                <IoArrowBackCircle size={30} />
                Retour
              </Button>
            </LinkContainer>
          </div>
          <div className="basis-10/16 p-1">
            <h1 className="text-2xl/7 font-bold text-white sm:truncate sm:text-3xl sm:tracking-tight">
              {title}
            </h1>
          </div>
          <div className="align-right basis-3/16">
            <LinkContainer to={`${instancePath}/0`}>
              <Button
                className="text-white"
                radius="full"
                size="lg"
                variant="light"
              >
                <icon.IoAddCircle size={30} />
                Nouveau
              </Button>
            </LinkContainer>
          </div>
        </div>

        <div className="d-flex justify-content-center flex flex-row">
          <div className="basis-3/16" />
          <div className="basis-7/16 p-1">
            <Input
              isClearable
              classNames={{
                label: "text-black/50 dark:text-white/90",
                input: [
                  "bg-transparent",
                  "text-black/90 dark:text-white/90",
                  "placeholder:text-default-700/50 dark:placeholder:text-white/60",
                ],
                innerWrapper: "bg-transparent",
                inputWrapper: [
                  "shadow-sm",
                  "bg-default-200/50",
                  "dark:bg-default/60",
                  "backdrop-blur-xl",
                  "backdrop-saturate-200",
                  "hover:bg-default-200/70",
                  "dark:hover:bg-default/70",
                  "group-data-[focus=true]:bg-default-200/50",
                  "dark:group-data-[focus=true]:bg-default/60",
                  "cursor-text!",
                ],
              }}
              label="Recherche"
              placeholder="Entrez des mots de recherche..."
              radius="lg"
              startContent={
                <SearchIcon className="text-black/50 mb-0.5 dark:text-white/90 text-slate-400 pointer-events-none shrink-0" />
              }
              value={search}
              onChange={(e) => setSearch(e.target.value.toLowerCase())}
            />
          </div>
          <div className="basis-3/16 p-1">
            <Select
              className="max-w-xs"
              defaultSelectedKeys={['{"key": "number", "sign": 1}']}
              label="Triage"
              onChange={(event) => setSort(event.target.value)}
            >
              {sortOptions.map((option) => (
                <SelectItem key={option.value}>{option.label}</SelectItem>
              ))}
            </Select>
          </div>
          <div className="basis-3/16" />
        </div>
      </div>
      <Modal isOpen={isOpen} onOpenChange={onOpenChange}>
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader className="flex flex-col gap-1">
                Supression Client
              </ModalHeader>
              <ModalBody>
                <p>
                  Êtes vous sûr de vouloir suprimmer <b>{nameToDelete}</b>?
                  Cette action est irréversible.
                </p>
              </ModalBody>
              <ModalFooter>
                <Button
                  color="danger"
                  variant="light"
                  onPress={() => {
                    deleteElement();
                    onClose();
                  }}
                >
                  Oui, Suprimmer
                </Button>
                <Button
                  color="success"
                  onPress={() => {
                    setNameToDelete("");
                    setIdToDelete(0);
                    setNumberToDelete(0);
                    onClose();
                  }}
                >
                  Non, Annuler
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
      <ProjectTable
        attribute1={attribute1}
        attribute2={attribute2}
        attribute3={attribute3}
        content={shownContent}
        height={tableHeight}
        isLoading={isLoading}
        pathname={instancePath}
        onDelete={openDeleteModal}
        onPrint={printElement}
      />
    </div>
  );
};

export default ProjectPage;
