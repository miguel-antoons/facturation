import { Textarea, Input } from "@heroui/input";
import { Divider } from "@heroui/divider";

const OrderLine = ({
  lineNumber = 1,
  writeOrderCell,
  orderInfo,
}: {
  lineNumber: number;
  writeOrderCell: (
    index: number,
    attribute: string,
    value: string | number,
  ) => void;
  orderInfo: {
    key: number;
    description: string;
    unitPrice: string;
    quantity: string;
    unit: string;
  };
}) => {
  const descriptionLabel = `Ligne de commande ${lineNumber}`;

  return (
    <>
      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/1 md:basis-4/8 p-2 pt-1 pb-1">
          <Divider />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/1 md:basis-4/8 p-2 pt-1 pb-1">
          <Textarea
            label={descriptionLabel}
            minRows={2}
            placeholder="Entrez une Description"
            value={orderInfo.description}
            onChange={(event) =>
              writeOrderCell(orderInfo.key, "description", event.target.value)
            }
          />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>

      <div className="flex flex-row">
        <div className="basis-2/8 hidden md:block" />
        <div className="basis-1/3 md:basis-1/6 pt-1 pb-1 pl-2 pr-1">
          <Input
            label="Pris excl. TVA"
            placeholder="0.00"
            startContent={
              <div className="pointer-events-none flex items-center">
                <span className="text-default-400 text-small">€</span>
              </div>
            }
            step="0.01"
            type="number"
            value={orderInfo.unitPrice}
            onChange={(event) =>
              writeOrderCell(orderInfo.key, "unitPrice", event.target.value)
            }
          />
        </div>
        <div className="basis-1/3 md:basis-1/6 p-1">
          <Input
            label="Quantité"
            placeholder="1.00"
            type="number"
            value={orderInfo.quantity}
            onChange={(event) =>
              writeOrderCell(orderInfo.key, "quantity", event.target.value)
            }
          />
        </div>
        <div className="basis-1/3 md:basis-1/6 pt-1 pb-1 pl-1 pr-2">
          <Input
            label="Unité"
            type="text"
            value={orderInfo.unit}
            onChange={(event) =>
              writeOrderCell(orderInfo.key, "unit", event.target.value)
            }
          />
        </div>
        <div className="basis-2/8 hidden md:block" />
      </div>
    </>
  );
};

export default OrderLine;
