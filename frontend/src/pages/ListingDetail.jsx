import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { MapPin, Bed, Bath, Maximize2, Layers, Phone, MessageSquare, ShieldCheck, Calculator } from 'lucide-react';
import api from '../api/client';
import InquiryModal from '../components/InquiryModal';
import BookingModal from '../components/BookingModal';
import { useTranslation } from '../i18n/i18nContext';
import styles from './ListingDetail.module.css';

const ListingDetail = () => {
  const { id } = useParams();
  const { t, language } = useTranslation();
  const [listing, setListing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedPhoto, setSelectedPhoto] = useState('');
  const [isInquiryOpen, setIsInquiryOpen] = useState(false);
  const [isBookingOpen, setIsBookingOpen] = useState(false);

  useEffect(() => {
    const fetchListing = async () => {
      try {
        const res = await api.get(`/listings/${id}/`);
        setListing(res.data);
        if (res.data.media && res.data.media.length > 0) {
          // Prefer is_primary image, fall back to first.
          const primary = res.data.media.find((m) => m.is_primary) || res.data.media[0];
          setSelectedPhoto(primary.url);
        } else {
          setSelectedPhoto('https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=800&q=80');
        }
      } catch (err) {
        console.error('Error fetching listing details:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchListing();
  }, [id]);

  if (loading) {
    return <div className={styles.loadingState}>{t('detail.loading')}</div>;
  }

  if (!listing) {
    return <div className={styles.emptyState}>{t('detail.notFound')}</div>;
  }

  const formatPrice = (price) => Number(price).toLocaleString(language === 'ar' ? 'ar-EG' : 'en-US');

  const whatsappMessage = encodeURIComponent(`Inquiring about property: ${listing.title} for ${formatPrice(listing.asking_price)} EGP`);
  const whatsappUrl = `https://wa.me/20${listing.seller_phone || '1000000000'}?text=${whatsappMessage}`;

  return (
    <div className={styles.page}>
      
      {/* Header Info */}
      <div className={styles.header}>
        <div className={styles.badges}>
          <span className={styles.badge}>
            {listing.type === 'resale' ? t('listings.resaleBadge') : t('listings.devBadge')}
          </span>
          <span className={styles.badge}>
            {listing.status}
          </span>
        </div>
        <h1 className={styles.pageTitle}>{listing.title}</h1>
        <div className={styles.locationRow}>
          <MapPin size={16} />
          <span>{listing.governorate} • {listing.city} {listing.district ? `(${listing.district})` : ''}</span>
        </div>
      </div>

      <div className={styles.layout}>
        
        {/* Left Column: Gallery & Facts */}
        <div>
          {/* Main Photo */}
          <div className={styles.mainPhoto}>
            <img src={selectedPhoto} alt={listing.title} />
          </div>

          {/* Thumbnails */}
          {listing.media && listing.media.length > 1 && (
            <div className={styles.thumbnails}>
              {listing.media.map((item) => (
                <img
                  key={item.id}
                  src={item.url}
                  alt="thumbnail"
                  onClick={() => setSelectedPhoto(item.url)}
                  className={`${styles.thumbnail} ${selectedPhoto === item.url ? styles.thumbnailActive : ''}`}
                />
              ))}
            </div>
          )}

          {/* Key Facts Box */}
          <div className={styles.factsBox}>
            <h3 className={styles.factsTitle}>{t('detail.specs')}</h3>
            <div className={styles.factsGrid}>
              <div className={styles.factCard}>
                <Maximize2 size={24} className={styles.factIcon} />
                <div className={styles.factLabel}>{t('detail.area')}</div>
                <strong className={styles.factValue}>{listing.area_sqm} {t('listings.m2')}</strong>
              </div>
              <div className={styles.factCard}>
                <Bed size={24} className={styles.factIcon} />
                <div className={styles.factLabel}>{t('detail.bedrooms')}</div>
                <strong className={styles.factValue}>{listing.bedrooms}</strong>
              </div>
              <div className={styles.factCard}>
                <Bath size={24} className={styles.factIcon} />
                <div className={styles.factLabel}>{t('detail.bathrooms')}</div>
                <strong className={styles.factValue}>{listing.bathrooms}</strong>
              </div>
              <div className={styles.factCard}>
                <Layers size={24} className={styles.factIcon} />
                <div className={styles.factLabel}>{t('detail.finishing')}</div>
                <strong className={styles.factValue}>{listing.finishing || 'N/A'}</strong>
              </div>
            </div>
          </div>

          {/* Description */}
          <div className={styles.descBox}>
            <h3 className={styles.descTitle}>{t('detail.detailsTitle')}</h3>
            <p className={styles.descText}>{listing.description || t('detail.noDescription')}</p>
          </div>

          {/* Installment Plan Breakdown */}
          {listing.installment_plan && (
            <div className={styles.calcBox}>
              <h3 className={styles.calcTitle}>
                <Calculator />
                {t('detail.takeoverCalculator')}
              </h3>
              <div className={styles.calcGrid}>
                <div>
                  <div className={styles.calcLabel}>{t('detail.paidAmount')}</div>
                  <strong className={styles.calcValue}>{formatPrice(listing.amount_paid || 0)} {t('listings.egp')}</strong>
                </div>
                <div>
                  <div className={styles.calcLabel}>{t('detail.transferFee')}</div>
                  <strong className={styles.calcValue}>{formatPrice(listing.transfer_fee || 0)} {t('listings.egp')}</strong>
                </div>
                <div>
                  <div className={styles.calcLabel}>{t('detail.quarterlyInstallment')}</div>
                  <strong className={styles.calcValue}>{formatPrice(listing.installment_plan.quarterly_installment || listing.installment_plan.quarterly || 0)} {t('listings.egp')}</strong>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Sticky Action Box */}
        <div>
          <div className={styles.sidebar}>
            
            <div className={styles.priceSection}>
              <span className={styles.priceLabel}>{t('detail.askingPrice')}:</span>
              <div className={styles.priceAmount}>
                {formatPrice(listing.asking_price)} <span className={styles.priceCurrency}>{t('listings.egp')}</span>
              </div>
              {listing.negotiable && <span className={styles.negotiableTag}>{t('listings.negotiable')}</span>}
            </div>

            <div className={styles.actionButtons}>
              
              <a href={whatsappUrl} target="_blank" rel="noreferrer" className={styles.whatsappBtn}>
                <MessageSquare size={18} />
                {t('detail.whatsapp')}
              </a>

              <a href={`tel:${listing.seller_phone || '01000000000'}`} className={styles.callBtn}>
                <Phone size={18} />
                {t('detail.call')}
              </a>

              <button onClick={() => setIsInquiryOpen(true)} className={styles.inquiryBtn}>
                {t('detail.inquiryBtn')}
              </button>

              <button onClick={() => setIsBookingOpen(true)} className={styles.bookBtn}>
                <ShieldCheck size={18} />
                {t('detail.bookBtn')}
              </button>

            </div>

          </div>
        </div>

      </div>

      {isInquiryOpen && <InquiryModal listing={listing} onClose={() => setIsInquiryOpen(false)} />}
      {isBookingOpen && <BookingModal listing={listing} onClose={() => setIsBookingOpen(false)} />}
    </div>
  );
};

export default ListingDetail;
