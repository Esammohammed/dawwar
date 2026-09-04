import React, { useEffect, useState } from 'react';
import api from '../../api/client';
import ListingCard from '../../components/ListingCard';
import FilterBar from '../../components/FilterBar';
import { useFilterStore } from '../../stores/filterStore';
import { useTranslation } from '../../i18n/i18nContext';
import styles from '../Listings.module.css';

const ExitOpportunities = () => {
  const { t } = useTranslation();
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sort, setSort] = useState('newest');
  const filters = useFilterStore();

  const fetchListings = async () => {
    setLoading(true);
    try {
      const params = { sort };
      if (filters.type) params.type = filters.type;
      if (filters.propertyType) params.property_type = filters.propertyType;
      if (filters.governorate) params.governorate = filters.governorate;
      if (filters.city) params.city = filters.city;
      if (filters.maxPrice) params.max_price = filters.maxPrice;
      if (filters.bedrooms) params.bedrooms = filters.bedrooms;
      if (filters.hasInstallments) params.has_installments = true;

      // We hit the dedicated opportunities endpoint which guarantees verification
      const res = await api.get('/listings/exit-opportunities/', { params });
      setListings(res.data.results || res.data || []);
    } catch (err) {
      console.error('Error fetching exit opportunities:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchListings();
  }, [filters.type, filters.propertyType, filters.governorate, filters.city, filters.maxPrice, filters.bedrooms, filters.hasInstallments, sort]);

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>{t('exitDeals.opportunitiesTitle')}</h1>
        <p className={styles.subtitle}>{t('exitDeals.subtitle')}</p>
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          style={{
            padding: '0.5rem 0.85rem', borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-strong)', background: 'var(--surface-subtle)',
            color: 'var(--text-main)', fontSize: '0.9rem',
          }}
        >
          <option value="newest">{t('exitDeals.sortNewest')}</option>
          <option value="cash_asc">{t('exitDeals.sortCashAsc')}</option>
          <option value="gain_desc">{t('exitDeals.sortGainDesc')}</option>
        </select>
      </div>

      <FilterBar onSearch={fetchListings} />

      {loading ? (
        <div className={styles.loadingState}>{t('listings.loading')}</div>
      ) : listings.length > 0 ? (
        <div className={styles.grid}>
          {listings.map((listing) => (
            <ListingCard key={listing.id} listing={listing} />
          ))}
        </div>
      ) : (
        <div className={styles.emptyState}>
          {t('listings.noResults')}
        </div>
      )}
    </div>
  );
};

export default ExitOpportunities;
