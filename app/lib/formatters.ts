export const formatCurrency = (amount: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);

export const formatShortCurrency = (amount: number) => {
  if (amount >= 10000000) {
    return `${formatCurrency(amount / 10000000).replace(".00", "")} Cr`;
  }

  return `${formatCurrency(amount / 100000).replace(".00", "")} L`;
};
