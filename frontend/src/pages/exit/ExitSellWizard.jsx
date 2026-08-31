import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, ArrowRight, ArrowLeft } from 'lucide-react';
import api from '../../api/client';
import { useAuthStore } from '../../stores/authStore';
import { useTranslation } from '../../i18n/i18nContext';
import styles from './ExitSellWizard.module.css';

const ExitSellWizard = () => {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const navigate = useNavigate();

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Step 1 fields
  const [title, setTitle] = useState('');
  const [originalPrice, setOriginalPrice] = useState('');
  const [amountPaid, setAmountPaid] = useState('');
  const [developerPrice, setDeveloperPrice] = useState('');
  const [description, setDescription] = useState('');
  const [noMarkup, setNoMarkup] = useState(false);

  // Step 2 fields
  const [contractFiles, setContractFiles] = useState([]);

  const handleNext = () => setStep(step + 1);
  const handlePrev = () => setStep(step - 1);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!user) {
      setError(t('auth.loginBtn'));
      return;
    }

    setLoading(true);
    setError('');

    try {
      // 1. Create base listing
      const { data: listing } = await api.post('/listings/', {
        type: 'resale',
        title: title || t('exitDeals.title'),
        description,
        original_price: parseFloat(originalPrice),
        amount_paid: parseFloat(amountPaid),
        installment_plan: { quarterly_installment: 0 },
        governorate: 'Giza',
        city: '6th of October',
        district: '',
        area_sqm: 100,
        bedrooms: 2,
        bathrooms: 1,
        floor: 1,
        finishing: 'fully',
        asking_price: parseFloat(amountPaid),
      });

      // 2. Attach exit profile
      await api.post(`/exit-deals/listings/${listing.id}/profile/`, {
        developer_current_price: developerPrice ? parseFloat(developerPrice) : null,
        owner_confirmed_no_markup: noMarkup,
      });

      // 3. Upload documents
      if (contractFiles.length > 0) {
        const docPayload = new FormData();
        Array.from(contractFiles).forEach((file) => docPayload.append('documents', file));
        docPayload.append('doc_type', 'contract');
        await api.post(`/exit-deals/listings/${listing.id}/documents/`, docPayload, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      }

      setStep(3);
    } catch (err) {
      console.error('Error creating exit deal:', err);
      const detail = err?.response?.data?.detail;
      setError(detail || 'Failed to save exit deal. Please check all fields.');
    } finally {
      setLoading(false);
    }
  };

  const step1Invalid = !title || !originalPrice || !amountPaid || !noMarkup;

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>{t('exitDeals.ctaSell')}</h1>
        <p className={styles.subtitle}>{t('exitDeals.title')} — {t('exitDeals.subtitle')}</p>
      </div>

      {error && <div className={styles.errorBox}>{error}</div>}

      <div className={styles.wizardCard}>

        {/* ── Step 1: Financials ── */}
        {step === 1 && (
          <div className={styles.step}>
            <h2>{t('exitDeals.wizardStep1Title')}</h2>

            <div className={styles.field}>
              <label>{t('exitDeals.wizardTitleLabel')}</label>
              <input type="text" value={title} onChange={e => setTitle(e.target.value)} required />
            </div>

            <div className={styles.field}>
              <label>{t('exitDeals.wizardOriginalPrice')}</label>
              <input type="number" value={originalPrice} onChange={e => setOriginalPrice(e.target.value)} required />
            </div>

            <div className={styles.field}>
              <label>{t('exitDeals.wizardAmountPaid')}</label>
              <input type="number" value={amountPaid} onChange={e => setAmountPaid(e.target.value)} required />
            </div>

            <div className={styles.field}>
              <label>{t('exitDeals.wizardDevPrice')}</label>
              <input type="number" value={developerPrice} onChange={e => setDeveloperPrice(e.target.value)} />
            </div>

            <div className={styles.field}>
              <label>{t('exitDeals.wizardDescription')}</label>
              <textarea value={description} onChange={e => setDescription(e.target.value)} rows={4} />
            </div>

            <div className={styles.checkboxWrapper}>
              <input
                type="checkbox"
                checked={noMarkup}
                onChange={e => setNoMarkup(e.target.checked)}
                id="noMarkup"
              />
              <label htmlFor="noMarkup">{t('exitDeals.wizardNoMarkup')}</label>
            </div>

            <div className={styles.actions}>
              <button className={styles.nextBtn} onClick={handleNext} disabled={step1Invalid}>
                {t('exitDeals.wizardNext')} <ArrowRight size={18} />
              </button>
            </div>
          </div>
        )}

        {/* ── Step 2: Documents ── */}
        {step === 2 && (
          <div className={styles.step}>
            <h2>{t('exitDeals.wizardStep2Title')}</h2>
            <p className={styles.infoText}>{t('exitDeals.wizardDocsInfo')}</p>

            <div className={styles.field}>
              <label>{t('exitDeals.wizardDocsLabel')}</label>
              <input
                type="file"
                multiple
                accept=".pdf,image/jpeg,image/png,image/webp"
                onChange={e => setContractFiles(e.target.files)}
              />
            </div>

            <div className={styles.actions}>
              <button className={styles.prevBtn} onClick={handlePrev}>
                <ArrowLeft size={18} /> {t('exitDeals.wizardBack')}
              </button>
              <button className={styles.submitBtn} onClick={handleSubmit} disabled={loading}>
                {loading ? t('exitDeals.wizardSubmitting') : t('exitDeals.wizardSubmit')}
              </button>
            </div>
          </div>
        )}

        {/* ── Step 3: Success ── */}
        {step === 3 && (
          <div className={styles.successStep}>
            <CheckCircle size={64} className={styles.successIcon} />
            <h2>{t('exitDeals.wizardSuccessTitle')}</h2>
            <p>{t('exitDeals.wizardSuccessDesc')}</p>
            <button className={styles.homeBtn} onClick={() => navigate('/exit/opportunities')}>
              {t('exitDeals.wizardViewOpps')}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExitSellWizard;
