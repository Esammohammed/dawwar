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
  const filters = useFilterStore();

  const fetchListings = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.type) params.type = filters.type;
      if (filters.propertyType) params.property_type = filters.propertyType;
      if (filters.governorate) params.governorate = filters.governorate;
      if (filters.city) params.city = filters.city;
      if (filters.maxPrice) params.max_price = filters.maxPrice;
      if (filters.bedrooms) params.bedrooms = filters.bedrooms;
      if (filters.hasInstallments) params.has_installments = true;

      // We hit the dedicated opportunities endpoint which guarantees verification
      const res = await api.get('/exit-deals/opportunities/', { params });
      setListings(res.data.results || res.data || []);
    } catch (err) {
      console.error('Error fetching exit opportunities:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchListings();
  }, [filters.type, filters.propertyType, filters.governorate, filters.city, filters.maxPrice, filters.bedrooms, filters.hasInstallments]);

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>{t('exitDeals.opportunitiesTitle')}</h1>
        <p className={styles.subtitle}>{t('exitDeals.subtitle')}</p>
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
