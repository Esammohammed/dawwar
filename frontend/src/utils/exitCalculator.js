export const calculateExitOptions = (contractPrice, paidToDate, yearsPaid) => {
  const price = parseFloat(contractPrice) || 0;
  const paid = parseFloat(paidToDate) || 0;
  const years = parseFloat(yearsPaid) || 0;

  if (!price || !paid) {
    return null;
  }

  // Transfer (Recover): Seller recovers exactly what they paid
  const transferRecovery = paid;

  // Cancel (Penalty): Typically 10% of the total contract price is deducted as a penalty
  const penaltyFactor = 0.10; 
  const penaltyAmount = price * penaltyFactor;
  const cancelRecovery = Math.max(0, paid - penaltyAmount);

  return {
    transferRecovery,
    cancelRecovery,
    penaltyAmount,
    difference: transferRecovery - cancelRecovery
  };
};
