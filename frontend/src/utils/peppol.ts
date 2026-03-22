const PeppolStatus = {
  NOT_SENT: -1,
  UNKNOWN: 0,
  PENDING: 1,
  RECEIVED: 2,
};

const isSentToPeppol = (peppolStatus: number) => {
  return (
    peppolStatus === PeppolStatus.PENDING ||
    peppolStatus === PeppolStatus.RECEIVED
  );
};

export { PeppolStatus, isSentToPeppol };
