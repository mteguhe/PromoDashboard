'use client';
import { useState } from 'react';

export default function PromoCard({ promo, category }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = (code) => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => {
      setCopied(false);
    }, 1500);
  };

  const isFlight = category === 'flight';
  const sourceLabel = promo.source_platform || 'Web';
  const subLabel = isFlight ? promo.airline : promo.brand_name;
  const detailRoute = isFlight 
    ? `${promo.origin_city || 'Jakarta'} ➔ ${promo.destination_city || 'Bali'}` 
    : `Min: ${promo.min_transaction || 'Tidak ada minimum'}`;

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-source">
          {sourceLabel}
        </span>
        {promo.expired_date && (
          <span className="card-expiry">
            Hingga: {promo.expired_date}
          </span>
        )}
      </div>
      <div className="card-body">
        <div className="card-brand">
          {subLabel}
        </div>
        <h3 className="card-title">
          {promo.title}
        </h3>
        <p className="card-desc">
          {promo.description}
        </p>
        
        {promo.discount_value && (
          <div className="discount-tag">{promo.discount_value}</div>
        )}

        {promo.promo_code ? (
          <div className="promo-code-container">
            <span>{promo.promo_code}</span>
            <button className="btn-copy" onClick={() => handleCopy(promo.promo_code)}>
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
        ) : (
          <div className="card-no-code">
            *Tidak memerlukan kode promo
          </div>
        )}

        {promo.terms_and_conditions && (
          <div className="card-terms">
            <strong>S&K:</strong> {promo.terms_and_conditions}
          </div>
        )}
      </div>
      <div className="card-footer">
        <span className="card-footer-detail">{detailRoute}</span>
        {promo.source_url && (
          <a href={promo.source_url} target="_blank" rel="noopener noreferrer" className="btn-link">
            Lihat Sumber ➔
          </a>
        )}
      </div>
    </div>
  );
}
