import React, { useState } from 'react';
import { Calculator, ArrowRight } from 'lucide-react';
import api from '../../api/client';
import { calculateExitOptions } from '../../utils/exitCalculator';
import { useTranslation } from '../../i18n/i18nContext';
import styles from './ExitCalculator.module.css';

const ExitCalculator = () => {
  const { t, language } = useTranslation();
  
  const [role, setRole] = useState('owner'); // 'buyer' or 'owner'
  const [contractPrice, setContractPrice] = useState('');
  const [paidToDate, setPaidToDate] = useState('');
  const [yearsPaid, setYearsPaid] = useState('');
  const [phone, setPhone] = useState('');
  const [submittedLead, setSubmittedLead] = useState(false);

  const result = calculateExitOptions(contractPrice, paidToDate, yearsPaid);

  const formatPrice = (price) => {
    return Number(price).toLocaleString(language === 'ar' ? 'ar-EG' : 'en-US');
  };

  const handleLeadSubmit = async (e) => {
    e.preventDefault();
    if (!result) return;

    try {
      await api.post('/exit-deals/calculator-leads/', {
        phone,
        contract_price: contractPrice,
        amount_paid: paidToDate,
        years_paid: yearsPaid,
        computed_result: result
      });
      setSubmittedLead(true);
      setPhone('');
    } catch (err) {
      console.error('Failed to submit lead', err);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>
          <Calculator className={styles.icon} />
          {t('exitDeals.calcTitle')}
        </h1>
      </div>

      <div className={styles.toggleGroup}>
        <button 
          className={`${styles.toggleBtn} ${role === 'buyer' ? styles.active : ''}`}
          onClick={() => setRole('buyer')}
        >
          {t('exitDeals.calcBuyer')}
        </button>
        <button 
          className={`${styles.toggleBtn} ${role === 'owner' ? styles.active : ''}`}
          onClick={() => setRole('owner')}
        >
          {t('exitDeals.calcOwner')}
        </button>
      </div>

      <div className={styles.calculatorCard}>
        <div className={styles.inputs}>
          <div className={styles.field}>
            <label>{t('exitDeals.contractPrice')}</label>
            <input 
              type="number" 
              value={contractPrice} 
              onChange={(e) => setContractPrice(e.target.value)}
              placeholder="e.g. 5000000"
            />
          </div>
          <div className={styles.field}>
            <label>{t('exitDeals.paidToDate')}</label>
            <input 
              type="number" 
              value={paidToDate} 
              onChange={(e) => setPaidToDate(e.target.value)}
              placeholder="e.g. 1000000"
            />
          </div>
          <div className={styles.field}>
            <label>{t('exitDeals.yearsPaid')}</label>
            <input 
              type="number" 
              value={yearsPaid} 
              onChange={(e) => setYearsPaid(e.target.value)}
              placeholder="e.g. 2"
            />
          </div>
        </div>

        {result && (
          <div className={styles.results}>
            <p className={styles.disclaimer}>{t('exitDeals.calcResultIndicative')}</p>
            
            <div className={styles.comparisonGrid}>
              <div className={styles.resultBoxPenalty}>
                <h3>{t('exitDeals.calcPenalty')}</h3>
                <div className={styles.value}>{formatPrice(result.cancelRecovery)}</div>
                <div className={styles.subtext}>
                  (Penalty: {formatPrice(result.penaltyAmount)})
                </div>
              </div>
              
              <div className={styles.resultBoxRecover}>
                <h3>{t('exitDeals.calcTransfer')}</h3>
                <div className={styles.value}>{formatPrice(result.transferRecovery)}</div>
                <div className={styles.subtext}>
                  (Full amount paid)
                </div>
              </div>
            </div>

            <div className={styles.leadCapture}>
              <h4>{t('exitDeals.calcLeadCta')}</h4>
              {submittedLead ? (
                <div className={styles.successMsg}>
                  We have received your request and will contact you shortly.
                </div>
              ) : (
                <form className={styles.leadForm} onSubmit={handleLeadSubmit}>
                  <input 
                    type="tel" 
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="Enter your phone number"
                    required
                  />
                  <button type="submit">
                    <ArrowRight size={18} />
                  </button>
                </form>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExitCalculator;
