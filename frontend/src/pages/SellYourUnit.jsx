import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle } from 'lucide-react';
import api from '../api/client';
import { useAuthStore } from '../stores/authStore';
import { useTranslation } from '../i18n/i18nContext';
import { GovernorateSelect, CitySelect } from '../components/LocationSelects';
import styles from './SellYourUnit.module.css';

const SellYourUnit = () => {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

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
    photo_url: 'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=600&q=80',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleGovernorateChange = (e) => {
    const { value } = e.target;
    setFormData((prev) => ({ ...prev, governorate: value, city: '' }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!user) {
      setError('Please login first to submit a listing.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await api.post('/listings/', {
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
          quarterly_installment: parseFloat(formData.quarterly_installment)
        },
        description: formData.description,
        uploaded_media: [formData.photo_url]
      });

      setStep(4);
    } catch (err) {
      console.error('Error creating resale listing:', err);
      setError('Failed to save listing. Please check required fields.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      
      <div className={styles.pageHeader}>
        <h1 className={styles.title}>{t('sell.title')}</h1>
        <p className={styles.subtitle}>{t('sell.subtitle')}</p>
      </div>

      {error && (
        <div className={styles.errorBox}>{error}</div>
      )}

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

          {step === 3 && (
            <div>
              <h3 className={styles.stepTitle}>{t('sell.step3Title')}</h3>

              <div className={styles.field}>
                <label className={styles.label}>{t('sell.photoUrlLabel')}</label>
                <input
                  type="text"
                  name="photo_url"
                  value={formData.photo_url}
                  onChange={handleChange}
                  className={styles.input}
                />
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
