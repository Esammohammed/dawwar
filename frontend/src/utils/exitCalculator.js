/**
 * صفقة دوّار — Safe Exit calculator.
 *
 * Compares two outcomes for someone stuck with an installment contract they
 * can't keep up with: cancelling it outright (developers apply a forfeiture
 * penalty per their own contract's cancellation clause) vs. transferring it
 * to a new buyer (recovers the full amount paid to date, since صفقة دوّار's
 * whole promise is no markup for the seller).
 *
 * The real cancellation-penalty schedule is set by each individual developer
 * contract and isn't public — AqarExit's own calculator doesn't publish its
 * exact formula either. DEFAULT_CANCELLATION_PENALTY_RATE below is a
 * deliberately simple placeholder assumption, not a researched figure; the
 * UI must always label this result "استرشادية" / indicative-only, never as
 * a precise quote.
 */

// Placeholder assumption only — see module docstring above.
export const DEFAULT_CANCELLATION_PENALTY_RATE = 0.10;

// yearsPaid is collected (matching AqarExit's own 3-input calculator) but not
// yet used in the math below — a real penalty schedule is typically
// time-graded, so this is kept as an input ready for that refinement rather
// than dropped from the form now and re-added later.
export const calculateExitOptions = (contractPrice, paidToDate, yearsPaid) => {
  const price = parseFloat(contractPrice) || 0;
  const paid = parseFloat(paidToDate) || 0;
  void yearsPaid;

  if (!price || !paid) {
    return null;
  }

  // Transfer: seller recovers exactly what they paid — no markup.
  const transferRecovery = paid;

  // Cancel: a flat indicative penalty deducted from what's paid so far.
  const penaltyAmount = price * DEFAULT_CANCELLATION_PENALTY_RATE;
  const cancelRecovery = Math.max(0, paid - penaltyAmount);

  return {
    transferRecovery,
    cancelRecovery,
    penaltyAmount,
    difference: transferRecovery - cancelRecovery,
  };
};
