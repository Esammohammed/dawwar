import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, ArrowRight, ArrowLeft } from 'lucide-react';
import api from '../../api/client';
import { useAuthStore } from '../../stores/authStore';
import { useTranslation } from '../../i18n/i18nContext';
import { GovernorateSelect, CitySelect } from '../../components/LocationSelects';
import FileDropZone from '../../components/FileDropZone';
import styles from './ExitSellWizard.module.css';

const PROPERTY_TYPES = ['Apartment', 'Villa', 'Townhouse', 'Penthouse', 'Chalet', 'Twin House', 'Duplex'];

const TOTAL_STEPS = 4;

const ExitSellWizard = () => {
  const { t, language } = useTranslation();
  const { user } = useAuthStore();
  const navigate = useNavigate();

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Step 1 — contract & financials
  const [title, setTitle] = useState('');
  const [originalPrice, setOriginalPrice] = useState('');
  const [amountPaid, setAmountPaid] = useState('');
  const [developerPrice, setDeveloperPrice] = useState('');
  const [noMarkup, setNoMarkup] = useState(false);

  // Step 2 — property specs & location
  const [governorate, setGovernorate] = useState('');
  const [city, setCity] = useState('');
  const [propertyType, setPropertyType] = useState('Apartment');
  const [areaSqm, setAreaSqm] = useState('');
  const [bedrooms, setBedrooms] = useState('');
  const [bathrooms, setBathrooms] = useState('');
  const [description, setDescription] = useState('');

  // Step 3 — documents & photos
  const [contractFiles, setContractFiles] = useState([]);
  const [receiptFiles, setReceiptFiles] = useState([]);
  const [photoFiles, setPhotoFiles] = useState([]);
  const [ownerOnly, setOwnerOnly] = useState(false);

  const formatPrice = (price) => Number(price || 0).toLocaleString(language === 'ar' ? 'ar-EG' : 'en-US');

  const handleNext = () => setStep((s) => Math.min(s + 1, TOTAL_STEPS));
  const handlePrev = () => setStep((s) => Math.max(s - 1, 1));

  const step1Invalid = !title || !originalPrice || !amountPaid || !noMarkup;
  const step2Invalid = !governorate || !city || !areaSqm || !bedrooms || !bathrooms;
  const step4Invalid = contractFiles.length === 0 || !ownerOnly;

  const uploadMedia = async (listingId, files, kind) => {
    if (files.length === 0) return;
    const payload = new FormData();
    files.forEach((file) => payload.append('images', file));
    payload.append('kind', kind);
    await api.post(`/listings/${listingId}/upload-media/`, payload, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!user) {
      setError(t('auth.loginBtn'));
      return;
    }

    setLoading(true);
    setError('');

    try {
      // 1. Create the listing — is_exit_listing carries all the صفقة دوّار
      //    metadata directly, no separate "profile" call needed anymore.
      const { data: listing } = await api.post('/listings/', {
        type: 'resale',
        title,
        description,
        governorate,
        city,
        property_type: propertyType,
        area_sqm: parseFloat(areaSqm),
        bedrooms: parseInt(bedrooms, 10),
        bathrooms: parseInt(bathrooms, 10),
        original_price: parseFloat(originalPrice),
        amount_paid: parseFloat(amountPaid),
        // The whole promise of صفقة دوّار is that the buyer pays exactly what
        // the seller paid — no markup — so the asking price is the recovered
        // amount, not a separately negotiated figure.
        asking_price: parseFloat(amountPaid),
        negotiable: false,
        is_exit_listing: true,
        owner_confirmed_no_markup: noMarkup,
        developer_current_price: developerPrice ? parseFloat(developerPrice) : null,
      });

      // 2. Upload documents and photos — same upload-media endpoint used by
      //    the regular sell flow, differentiated only by `kind`.
      await uploadMedia(listing.id, contractFiles, 'contract');
      await uploadMedia(listing.id, receiptFiles, 'payment_receipt');
      await uploadMedia(listing.id, photoFiles, 'photo');

      setStep(5);
    } catch (err) {
      console.error('Error creating صفقة دوّار listing:', err);
      const detail = err?.response?.data?.detail || err?.response?.data?.owner_confirmed_no_markup?.[0];
      setError(detail || 'Failed to save listing. Please check all fields.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>{t('exitDeals.ctaSell')}</h1>
        <p className={styles.subtitle}>{t('exitDeals.title')} — {t('exitDeals.subtitle')}</p>
      </div>

      {error && <div className={styles.errorBox}>{error}</div>}

      {step <= TOTAL_STEPS && (
        <div className={styles.progress}>
          {Array.from({ length: TOTAL_STEPS }).map((_, i) => (
            <span key={i} className={`${styles.progressSeg} ${i < step ? styles.progressSegDone : ''}`} />
          ))}
        </div>
      )}

      <div className={styles.wizardCard}>

        {/* ── Step 1: Contract & Financials ── */}
        {step === 1 && (
          <div className={styles.step}>
            <h2>{t('exitDeals.wizardStep1Title')}</h2>

            <div className={styles.field}>
              <label>{t('exitDeals.wizardTitleLabel')}</label>
              <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} required />
            </div>

            <div className={styles.grid2}>
              <div className={styles.field}>
                <label>{t('exitDeals.wizardOriginalPrice')}</label>
                <input type="number" value={originalPrice} onChange={(e) => setOriginalPrice(e.target.value)} required />
              </div>
              <div className={styles.field}>
                <label>{t('exitDeals.wizardAmountPaid')}</label>
                <input type="number" value={amountPaid} onChange={(e) => setAmountPaid(e.target.value)} required />
              </div>
            </div>

            <div className={styles.field}>
              <label>{t('exitDeals.wizardDevPrice')}</label>
              <input type="number" value={developerPrice} onChange={(e) => setDeveloperPrice(e.target.value)} />
            </div>

            <div className={styles.checkboxWrapper}>
              <input type="checkbox" checked={noMarkup} onChange={(e) => setNoMarkup(e.target.checked)} id="noMarkup" />
              <label htmlFor="noMarkup">{t('exitDeals.wizardNoMarkup')}</label>
            </div>

            <div className={styles.actions}>
              <button type="button" className={styles.nextBtn} onClick={handleNext} disabled={step1Invalid}>
                {t('exitDeals.wizardNext')} <ArrowRight size={18} />
              </button>
            </div>
          </div>
        )}

        {/* ── Step 2: Property specs & location ── */}
        {step === 2 && (
          <div className={styles.step}>
            <h2>{t('exitDeals.wizardStep2Title')}</h2>

            <div className={styles.grid2}>
              <div className={styles.field}>
                <label>{t('exitDeals.wizardGovLabel')}</label>
                <GovernorateSelect
                  value={governorate}
                  onChange={(e) => { setGovernorate(e.target.value); setCity(''); }}
                  required
                />
              </div>
              <div className={styles.field}>
                <label>{t('exitDeals.wizardCityLabel')}</label>
                <CitySelect
                  governorate={governorate}
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className={styles.field}>
              <label>{t('exitDeals.wizardPropertyTypeLabel')}</label>
              <select value={propertyType} onChange={(e) => setPropertyType(e.target.value)}>
                {PROPERTY_TYPES.map((pt) => <option key={pt} value={pt}>{pt}</option>)}
              </select>
            </div>

            <div className={styles.grid3}>
              <div className={styles.field}>
                <label>{t('exitDeals.wizardAreaLabel')}</label>
                <input type="number" value={areaSqm} onChange={(e) => setAreaSqm(e.target.value)} required />
              </div>
              <div className={styles.field}>
                <label>{t('exitDeals.wizardBedroomsLabel')}</label>
                <input type="number" value={bedrooms} onChange={(e) => setBedrooms(e.target.value)} required />
              </div>
              <div className={styles.field}>
                <label>{t('exitDeals.wizardBathroomsLabel')}</label>
                <input type="number" value={bathrooms} onChange={(e) => setBathrooms(e.target.value)} required />
              </div>
            </div>

            <div className={styles.field}>
              <label>{t('exitDeals.wizardDescription')}</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
                placeholder={t('exitDeals.wizardDescPlaceholder')}
              />
            </div>

            <div className={styles.actions}>
              <button type="button" className={styles.prevBtn} onClick={handlePrev}>
                <ArrowLeft size={18} /> {t('exitDeals.wizardBack')}
              </button>
              <button type="button" className={styles.nextBtn} onClick={handleNext} disabled={step2Invalid}>
                {t('exitDeals.wizardNext')} <ArrowRight size={18} />
              </button>
            </div>
          </div>
        )}

        {/* ── Step 3: Documents & photos ── */}
        {step === 3 && (
          <div className={styles.step}>
            <h2>{t('exitDeals.wizardStep3Title')}</h2>
            <p className={styles.infoText}>{t('exitDeals.wizardDocsInfo')}</p>

            <div className={styles.field}>
              <label>{t('exitDeals.wizardContractLabel')}</label>
              <FileDropZone
                files={contractFiles}
                onChange={setContractFiles}
                accept="application/pdf,image/jpeg,image/png"
                maxFiles={5}
                maxSizeMB={10}
                label={t('exitDeals.wizardContractLabel')}
                hint={t('exitDeals.wizardContractHint')}
              />
            </div>

            <div className={styles.field}>
              <label>{t('exitDeals.wizardReceiptLabel')}</label>
              <FileDropZone
                files={receiptFiles}
                onChange={setReceiptFiles}
                accept="application/pdf,image/jpeg,image/png"
                maxFiles={5}
                maxSizeMB={10}
                label={t('exitDeals.wizardReceiptLabel')}
                hint={t('exitDeals.wizardReceiptHint')}
              />
            </div>

            <div className={styles.field}>
              <label>{t('exitDeals.wizardPhotosLabel')}</label>
              <FileDropZone
                files={photoFiles}
                onChange={setPhotoFiles}
                accept="image/jpeg,image/png,image/webp"
                maxFiles={10}
                maxSizeMB={10}
                label={t('exitDeals.wizardPhotosLabel')}
                hint={t('exitDeals.wizardPhotosHint')}
              />
            </div>

            <div className={styles.checkboxWrapper}>
              <input type="checkbox" checked={ownerOnly} onChange={(e) => setOwnerOnly(e.target.checked)} id="ownerOnly" />
              <label htmlFor="ownerOnly">{t('exitDeals.wizardOwnerOnly')}</label>
            </div>

            <div className={styles.actions}>
              <button type="button" className={styles.prevBtn} onClick={handlePrev}>
                <ArrowLeft size={18} /> {t('exitDeals.wizardBack')}
              </button>
              <button type="button" className={styles.nextBtn} onClick={handleNext} disabled={step4Invalid}>
                {t('exitDeals.wizardNext')} <ArrowRight size={18} />
              </button>
            </div>
          </div>
        )}

        {/* ── Step 4: Review & submit ── */}
        {step === 4 && (
          <form className={styles.step} onSubmit={handleSubmit}>
            <h2>{t('exitDeals.wizardStep4Title')}</h2>
            <p className={styles.infoText}>{t('exitDeals.wizardReviewNote')}</p>

            <div className={styles.reviewGrid}>
              <div className={styles.reviewRow}><span>{t('exitDeals.wizardTitleLabel')}</span><strong>{title}</strong></div>
              <div className={styles.reviewRow}><span>{t('exitDeals.wizardGovLabel')} / {t('exitDeals.wizardCityLabel')}</span><strong>{governorate} — {city}</strong></div>
              <div className={styles.reviewRow}><span>{t('exitDeals.wizardOriginalPrice')}</span><strong>{formatPrice(originalPrice)} {t('listings.egp')}</strong></div>
              <div className={styles.reviewRow}><span>{t('exitDeals.wizardReviewCash')}</span><strong>{formatPrice(amountPaid)} {t('listings.egp')}</strong></div>
              <div className={styles.reviewRow}><span>{t('exitDeals.wizardContractLabel')}</span><strong>{contractFiles.length}</strong></div>
              <div className={styles.reviewRow}><span>{t('exitDeals.wizardPhotosLabel')}</span><strong>{photoFiles.length}</strong></div>
            </div>

            <div className={styles.actions}>
              <button type="button" className={styles.prevBtn} onClick={handlePrev}>
                <ArrowLeft size={18} /> {t('exitDeals.wizardBack')}
              </button>
              <button type="submit" className={styles.submitBtn} disabled={loading}>
                {loading ? t('exitDeals.wizardSubmitting') : t('exitDeals.wizardSubmit')}
              </button>
            </div>
          </form>
        )}

        {/* ── Success ── */}
        {step === 5 && (
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
