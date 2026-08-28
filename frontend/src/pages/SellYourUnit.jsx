import React, { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, UploadCloud, X, ImagePlus } from 'lucide-react';
import api from '../api/client';
import { useAuthStore } from '../stores/authStore';
import { useTranslation } from '../i18n/i18nContext';
import { GovernorateSelect, CitySelect } from '../components/LocationSelects';
import styles from './SellYourUnit.module.css';

// ─── Constants ────────────────────────────────────────────────────────────────

const MAX_IMAGES = 10;
const MAX_FILE_SIZE_MB = 10;
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

// ─── ImageUploadZone ─────────────────────────────────────────────────────────

/**
 * Drag-and-drop / click-to-browse image upload zone.
 * Manages local preview URLs; actual upload happens on form submit.
 */
const ImageUploadZone = ({ files, onChange }) => {
  const { t } = useTranslation();
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const addFiles = useCallback(
    (incoming) => {
      const valid = [];
      const errors = [];

      for (const file of incoming) {
        if (!ALLOWED_TYPES.includes(file.type)) {
          errors.push(`"${file.name}" is not a supported format (JPEG, PNG, WebP only).`);
          continue;
        }
        if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
          errors.push(`"${file.name}" exceeds ${MAX_FILE_SIZE_MB} MB.`);
          continue;
        }
        if (files.length + valid.length >= MAX_IMAGES) {
          errors.push(`Maximum ${MAX_IMAGES} images allowed.`);
          break;
        }
        valid.push(file);
      }

      if (errors.length) alert(errors.join('\n'));
      if (valid.length) onChange([...files, ...valid]);
    },
    [files, onChange]
  );

  const removeFile = (index) => {
    const next = files.filter((_, i) => i !== index);
    onChange(next);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    addFiles(Array.from(e.dataTransfer.files));
  };

  const handleInputChange = (e) => {
    addFiles(Array.from(e.target.files));
    // Reset input so the same file can be re-selected after removal.
    e.target.value = '';
  };

  return (
    <div className={styles.uploadSection}>
      {/* Drop zone */}
      <div
        className={`${styles.dropZone} ${dragging ? styles.dropZoneDragging : ''}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
        aria-label={t('sell.uploadZoneLabel')}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ALLOWED_TYPES.join(',')}
          multiple
          className={styles.hiddenInput}
          onChange={handleInputChange}
        />
        <UploadCloud className={styles.uploadIcon} size={40} />
        <p className={styles.uploadPrimary}>{t('sell.uploadPrimary')}</p>
        <p className={styles.uploadSecondary}>
          {t('sell.uploadSecondary', { max: MAX_IMAGES, size: MAX_FILE_SIZE_MB })}
        </p>
      </div>

      {/* Preview grid */}
      {files.length > 0 && (
        <div className={styles.previewGrid}>
          {files.map((file, index) => (
            <div key={index} className={styles.previewItem}>
              <img
                src={URL.createObjectURL(file)}
                alt={file.name}
                className={styles.previewImg}
              />
              {index === 0 && (
                <span className={styles.primaryBadge}>{t('sell.primaryBadge')}</span>
              )}
              <button
                type="button"
                className={styles.removeBtn}
                onClick={() => removeFile(index)}
                aria-label={`Remove ${file.name}`}
              >
                <X size={14} />
              </button>
            </div>
          ))}

          {files.length < MAX_IMAGES && (
            <button
              type="button"
              className={styles.addMoreBtn}
              onClick={() => inputRef.current?.click()}
              aria-label={t('sell.addMore')}
            >
              <ImagePlus size={24} />
              <span>{t('sell.addMore')}</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
};

// ─── SellYourUnit ─────────────────────────────────────────────────────────────

const SellYourUnit = () => {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const navigate = useNavigate();

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [imageFiles, setImageFiles] = useState([]);

  const [formData, setFormData] = useState({
    title: '',
    governorate: 'Giza',
    city: '6th of October',
    district: '',
    area_sqm: 115,
    bedrooms: 3,
    bathrooms: 2,
    floor: 3,
    finishing: 'fully',
    asking_price: 1250000,
    original_price: 950000,
    amount_paid: 350000,
    transfer_fee: 25000,
    quarterly_installment: 25000,
    description: '',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleGovernorateChange = (e) => {
    setFormData((prev) => ({ ...prev, governorate: e.target.value, city: '' }));
  };

  // ── Submit ─────────────────────────────────────────────────────────────────

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!user) {
      setError('Please login first to submit a listing.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // 1️⃣  Create the listing with structured JSON data.
      const { data: listing } = await api.post('/listings/', {
        type: 'resale',
        title: formData.title,
        governorate: formData.governorate,
        city: formData.city,
        district: formData.district,
        area_sqm: parseFloat(formData.area_sqm),
        bedrooms: parseInt(formData.bedrooms),
        bathrooms: parseInt(formData.bathrooms),
        floor: parseInt(formData.floor),
        finishing: formData.finishing,
        asking_price: parseFloat(formData.asking_price),
        original_price: parseFloat(formData.original_price),
        amount_paid: parseFloat(formData.amount_paid),
        transfer_fee: parseFloat(formData.transfer_fee),
        installment_plan: {
          quarterly_installment: parseFloat(formData.quarterly_installment),
        },
        description: formData.description,
      });

      // 2️⃣  Upload images separately if any were selected.
      if (imageFiles.length > 0) {
        const formPayload = new FormData();
        imageFiles.forEach((file) => formPayload.append('images', file));

        await api.post(`/listings/${listing.id}/upload-media/`, formPayload, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      }

      setStep(4);
    } catch (err) {
      console.error('Error creating resale listing:', err);
      const detail = err?.response?.data?.detail;
      setError(detail || 'Failed to save listing. Please check required fields.');
    } finally {
      setLoading(false);
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}>{t('sell.title')}</h1>
        <p className={styles.subtitle}>{t('sell.subtitle')}</p>
      </div>

      {error && <div className={styles.errorBox}>{error}</div>}

      {step === 4 ? (
        <div className={styles.successCard}>
          <CheckCircle size={64} className={styles.successIcon} />
          <h2 className={styles.successTitle}>{t('sell.successTitle')}</h2>
          <p className={styles.successDesc}>{t('sell.successDesc')}</p>
          <button onClick={() => navigate('/account')} className={styles.successBtn}>
            {t('sell.goToAccount')}
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className={styles.formCard}>

          {/* ── Step 1: Unit Details ── */}
          {step === 1 && (
            <div>
              <h3 className={styles.stepTitle}>{t('sell.step1Title')}</h3>

              <div className={styles.field}>
                <label className={styles.label}>{t('sell.titleLabel')}</label>
                <input
                  type="text"
                  name="title"
                  value={formData.title}
                  onChange={handleChange}
                  placeholder={t('sell.titlePlaceholder')}
                  className={styles.input}
                  required
                />
              </div>

              <div className={styles.grid2}>
                <div className={styles.field}>
                  <label className={styles.label}>{t('sell.govLabel')}</label>
                  <GovernorateSelect
                    value={formData.governorate}
                    onChange={handleGovernorateChange}
                    className={styles.input}
                    required
                  />
                </div>
                <div className={styles.field}>
                  <label className={styles.label}>{t('sell.cityLabel')}</label>
                  <CitySelect
                    governorate={formData.governorate}
                    value={formData.city}
                    onChange={handleChange}
                    className={styles.input}
                    required
                  />
                </div>
              </div>

              <div className={styles.grid3}>
                <div className={styles.field}>
                  <label className={styles.label}>{t('sell.areaLabel')}</label>
                  <input
                    type="number"
                    name="area_sqm"
                    value={formData.area_sqm}
                    onChange={handleChange}
                    className={styles.input}
                    required
                  />
                </div>
                <div className={styles.field}>
                  <label className={styles.label}>{t('sell.bedroomsLabel')}</label>
                  <input
                    type="number"
                    name="bedrooms"
                    value={formData.bedrooms}
                    onChange={handleChange}
                    className={styles.input}
                    required
                  />
                </div>
                <div className={styles.field}>
                  <label className={styles.label}>{t('sell.bathroomsLabel')}</label>
                  <input
                    type="number"
                    name="bathrooms"
                    value={formData.bathrooms}
                    onChange={handleChange}
                    className={styles.input}
                    required
                  />
                </div>
              </div>

              <button type="button" onClick={() => setStep(2)} className={styles.nextBtn}>
                {t('sell.next')} →
              </button>
            </div>
          )}

          {/* ── Step 2: Financials ── */}
          {step === 2 && (
            <div>
              <h3 className={styles.stepTitle}>{t('sell.step2Title')}</h3>

              <div className={styles.field}>
                <label className={styles.label}>{t('sell.askingPriceLabel')}</label>
                <input
                  type="number"
                  name="asking_price"
                  value={formData.asking_price}
                  onChange={handleChange}
                  className={styles.input}
                  required
                />
              </div>

              <div className={styles.grid2}>
                <div className={styles.field}>
                  <label className={styles.label}>{t('sell.paidAmountLabel')}</label>
                  <input
                    type="number"
                    name="amount_paid"
                    value={formData.amount_paid}
                    onChange={handleChange}
                    className={styles.input}
                  />
                </div>
                <div className={styles.field}>
                  <label className={styles.label}>{t('sell.transferFeeLabel')}</label>
                  <input
                    type="number"
                    name="transfer_fee"
                    value={formData.transfer_fee}
                    onChange={handleChange}
                    className={styles.input}
                  />
                </div>
              </div>

              <div className={styles.field}>
                <label className={styles.label}>{t('sell.quarterlyLabel')}</label>
                <input
                  type="number"
                  name="quarterly_installment"
                  value={formData.quarterly_installment}
                  onChange={handleChange}
                  className={styles.input}
                />
              </div>

              <div className={styles.btnRow}>
                <button type="button" onClick={() => setStep(1)} className={styles.prevBtn}>
                  {t('sell.prev')}
                </button>
                <button type="button" onClick={() => setStep(3)} className={styles.nextBtn}>
                  {t('sell.next')} →
                </button>
              </div>
            </div>
          )}

          {/* ── Step 3: Photos & Description ── */}
          {step === 3 && (
            <div>
              <h3 className={styles.stepTitle}>{t('sell.step3Title')}</h3>

              <div className={styles.field}>
                <label className={styles.label}>{t('sell.photosLabel')}</label>
                <ImageUploadZone files={imageFiles} onChange={setImageFiles} />
              </div>

              <div className={styles.field}>
                <label className={styles.label}>{t('sell.descLabel')}</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  rows={4}
                  placeholder={t('sell.descPlaceholder')}
                  className={styles.textarea}
                />
              </div>

              <div className={styles.btnRow}>
                <button type="button" onClick={() => setStep(2)} className={styles.prevBtn}>
                  {t('sell.prev')}
                </button>
                <button type="submit" disabled={loading} className={styles.submitBtn}>
                  {loading ? t('sell.saving') : t('sell.submit')}
                </button>
              </div>
            </div>
          )}

        </form>
      )}
    </div>
  );
};

export default SellYourUnit;
