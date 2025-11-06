import "@/styles/projectTable.css";

import { Key } from "node:readline";

import * as icon from "react-icons/io5";
import { useNavigate } from "react-router-dom";
import { Button, ButtonGroup } from "@heroui/button";
import {
  Table,
  TableHeader,
  TableBody,
  TableColumn,
  TableRow,
  TableCell,
} from "@heroui/table";
import { Spinner } from "@heroui/spinner";
import React, { ReactNode } from "react";

const ProjectTable = ({
  content,
  onDelete,
  onPrint,
  height,
  pathname,
  attribute1,
  attribute2,
  attribute3,
  isLoading,
  customButtonText = (
    <>
      <icon.IoOpen size={20} /> Ouvrir
    </>
  ),
  customButtonAction = undefined,
}: {
  content: {
    id: number;
    number: number;
    attribute1: string;
    attribute2: string;
    attribute3: string;
    fileId: string | null;
  }[];
  onDelete: (id: number, number: number, name: string) => any;
  onPrint: (id: number | string | null) => any;
  height: number;
  pathname: string;
  attribute1: string;
  attribute2: string;
  attribute3: string;
  isLoading: boolean;
  customButtonText?: ReactNode;
  customButtonAction?: ((id: number) => any) | undefined;
}) => {
  const navigate = useNavigate();

  if (customButtonAction === undefined)
    customButtonAction = (id) => navigate(`${pathname}/${id}`);
  const columns = [
    {
      key: "number",
      name: "#",
      width: 25,
      maxWidth: 2000,
    },
    {
      key: "attribute1",
      name: attribute1,
      width: 300,
      maxWidth: 2000,
    },
    {
      key: "attribute2",
      name: attribute2,
      width: 150,
      maxWidth: 2000,
    },
    {
      key: "attribute3",
      name: attribute3,
      width: 150,
      maxWidth: 2000,
    },
    {
      key: "actions",
      name: "ACTIONS",
      width: "10%",
      maxWidth: 100,
    },
  ];

  const renderCell = React.useCallback(
    (
      element: {
        id: number;
        number: number;
        attribute1: string;
        attribute2: string;
        attribute3: string;
        fileId: string | null;
      },
      columnKey: string | Key | number,
    ) => {
      // @ts-ignore
      const cellValue: string | number = element[columnKey];

      switch (columnKey) {
        case "actions":
          return (
            <ClickKiller>
              <ButtonGroup>
                <Button
                  color="danger"
                  variant="flat"
                  onPress={() =>
                    onDelete(element.id, element.number, element.attribute1)
                  }
                >
                  <icon.IoTrash size={20} /> Suprimmer
                </Button>
                <Button
                  color="primary"
                  variant="flat"
                  onPress={() => onPrint(element.fileId)}
                >
                  <icon.IoPrint size={20} /> Imprimer
                </Button>
                <Button
                  color="primary"
                  variant="flat"
                  onPress={() => customButtonAction(element.id)}
                >
                  {customButtonText}
                </Button>
              </ButtonGroup>
            </ClickKiller>
          );
        default:
          return cellValue;
      }
    },
    [],
  );

  return (
    <Table
      isStriped
      isVirtualized
      aria-label="Project Table"
      maxTableHeight={height}
      onRowAction={(key) => navigate(`${pathname}/${key}`)}
    >
      <TableHeader columns={columns}>
        {(column) => (
          // @ts-ignore
          <TableColumn key={column.key} width={column.width}>
            {column.name}
          </TableColumn>
        )}
      </TableHeader>
      <TableBody
        isLoading={isLoading}
        items={content}
        loadingContent={<Spinner label="Chargement..." />}
      >
        {(item) => (
          <TableRow key={item.id}>
            {(columnKey) => (
              <TableCell>{renderCell(item, columnKey)}</TableCell>
            )}
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
};

const ClickKiller = ({ children }: { children: ReactNode }) => {
  // eslint-disable-next-line jsx-a11y/no-static-element-interactions,jsx-a11y/click-events-have-key-events
  return <div onClick={(e) => e.stopPropagation()}>{children}</div>;
};

export default ProjectTable;
