const projectNumberToNumber = (value: string) =>
  Number(value.replace(/\D/g, ""));

export { projectNumberToNumber };
