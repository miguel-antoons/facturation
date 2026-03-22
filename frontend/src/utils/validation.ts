const isBillitReady = (
  billIsSaved: boolean,
  orderLines: {
    key: number;
    description: string;
    quantity: string;
    unitPrice: string;
    unit: string;
  }[],
  billAlreadySentToBillit: boolean,
) => {
  if (billAlreadySentToBillit) {
    return {
      disabled: true,
      tooltipText: "La facture a déjà été envoyée à Billit.",
    };
  }

  if (!billIsSaved) {
    return {
      disabled: true,
      tooltipText: "Veuillez d'abord enregistrer la facture.",
    };
  }

  if (orderLines.length === 0) {
    return {
      disabled: true,
      tooltipText: "La facture doit contenir au moins une ligne de commande.",
    };
  }

  for (const line of orderLines) {
    if (
      line.description === "" ||
      line.quantity === "" ||
      line.unitPrice === ""
    ) {
      return {
        disabled: true,
        tooltipText:
          "Chaque ligne de commande doit avoir une description, une quantité et un prix unitaire.",
      };
    }
  }

  return {
    disabled: false,
    tooltipText: "",
  };
};

const cnoteIsBillitReady = (
  cnoteIsSaved: boolean,
  orderLines: {
    key: number;
    description: string;
    quantity: string;
    unitPrice: string;
    unit: string;
  }[],
  cnoteAlreadySentToBillit: boolean,
  aboutInvoiceNumber: string,
) => {
  let res = isBillitReady(cnoteIsSaved, orderLines, cnoteAlreadySentToBillit);

  if (
    !res.disabled &&
    (aboutInvoiceNumber === "" ||
      aboutInvoiceNumber === undefined ||
      aboutInvoiceNumber === null)
  ) {
    res = {
      disabled: true,
      tooltipText:
        "Veuillez remplir le champ 'Numéro de Facture Concernée' pour envoyer la note de crédit à Billit.",
    };
  }

  return res;
};

const isPeppolReady = (
  isSentToBillit: boolean,
  customerHasVAT: boolean,
  billAlreadySentToPeppol: boolean,
) => {
  // the bill must be sent to billit, customer must have a VAT number + requirements from isBillitRead
  if (billAlreadySentToPeppol) {
    return {
      disabled: true,
      tooltipText: "La facture a déjà été envoyée via Peppol.",
    };
  }

  if (!customerHasVAT) {
    return {
      disabled: true,
      tooltipText:
        "Le client doit avoir un numéro de TVA pour envoyer la facture via Peppol.",
    };
  }

  if (!isSentToBillit) {
    return {
      disabled: true,
      tooltipText: "Veuillez d'abord envoyer la facture à Billit.",
    };
  }

  return {
    disabled: false,
    tooltipText: "",
  };
};

const isSaveReady = (
  customerId: string,
  title: string,
  billNumber: string,
  isSentToBillit: boolean,
): { disabled: boolean; tooltipText: string } => {
  if (isSentToBillit) {
    return {
      disabled: true,
      tooltipText:
        "La facture a déjà été envoyée à Billit. Vous ne pouvez plus la modifier.",
    };
  }
  const customerEmpty =
    customerId === "" || customerId === undefined || customerId === null;
  const titleEmpty = title === "" || title === undefined || title === null;
  const billNumberEmpty =
    billNumber === "" || billNumber === undefined || billNumber === null;

  if (customerEmpty || titleEmpty || billNumberEmpty) {
    return {
      disabled: true,
      tooltipText:
        "Veuillez remplir les champs obligatoires : Client, Titre et Numéro de facture.",
    };
  }

  return {
    disabled: false,
    tooltipText: "",
  };
};

export { isBillitReady, isPeppolReady, isSaveReady, cnoteIsBillitReady };
