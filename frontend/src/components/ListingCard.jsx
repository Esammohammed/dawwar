import React from 'react';
import { Link } from 'react-router-dom';
import { MapPin, Bed, Bath, Maximize2 } from 'lucide-react';
import { useTranslation } from '../i18n/i18nContext';
import styles from './ListingCard.module.css';

const ListingCard = ({ listing }) => {
  const { t, language } = useTranslation();

  const coverPhoto = listing.media && listing.media.length > 0
    ? listing.media[0].file
    : 'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=600&q=80';

  const formatPrice = (price) => {
    return Number(price).toLocaleString(language === 'ar' ? 'ar-EG' : 'en-US');
  };

  return (
    <Link to={`/listings/${listing.id}`} className={styles.card}>
      <div className={styles.imageWrapper}>
        <img src={coverPhoto} alt={listing.title} className={styles.image} />
        
        <span className={styles.typeBadge}>
          {listing.type === 'resale' ? t('listings.resaleBadge') : t('listings.devBadge')}
        </span>

        {listing.installment_plan && (
          <span className={styles.installmentBadge}>
            {t('listings.installmentsBadge')}
          </span>
        )}
      </div>

      <div className={styles.content}>
        <div className={styles.location}>
          <MapPin size={14} />
          <span>{listing.governorate} • {listing.city} {listing.district ? `(${listing.district})` : ''}</span>
        </div>

        <h3 className={styles.title}>{listing.title}</h3>

        <div className={styles.facts}>
          <div className={styles.factItem}>
            <Bed size={16} />
            <span>{listing.bedrooms} {t('listings.beds')}</span>
          </div>
          <div className={styles.factItem}>
            <Bath size={16} />
            <span>{listing.bathrooms} {t('listings.baths')}</span>
          </div>
          <div className={styles.factItem}>
            <Maximize2 size={16} />
            <span>{listing.area_sqm} {t('listings.m2')}</span>
          </div>
        </div>

        <div className={styles.footer}>
          <div>
            <span className={styles.price}>{formatPrice(listing.asking_price)}</span>
            <span className={styles.currency}> {t('listings.egp')}</span>
          </div>

          <span style={{ fontSize: '0.8rem', color: '#0284c7', fontWeight: '700' }}>
            {t('listings.details')} →
          </span>
        </div>
      </div>
    </Link>
  );
};

export default ListingCard;
