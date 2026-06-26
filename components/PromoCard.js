'use client';

export default function PromoCard({ promo, category }) {
  const handleCopy = (code) => {
    navigator.clipboard.writeText(code);
    alert('Kode promo berhasil disalin: ' + code);
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
        <span style={{ fontSize: '0.8em', color: 'var(--text-muted)', fontWeight: 'bold' }}>
          {sourceLabel}
        </span>
        {promo.expired_date && (
          <span style={{ fontSize: '0.75em', background: 'var(--accent)', color: '#fff', padding: '2px 6px', borderRadius: '4px' }}>
            Hingga: {promo.expired_date}
          </span>
        )}
      </div>
      <div className="card-body">
        <div style={{ fontSize: '0.8em', textTransform: 'uppercase', color: 'var(--primary)', fontWeight: 'bold', marginBottom: '5px' }}>
          {subLabel}
        </div>
        <h3 style={{ margin: '0 0 10px 0', fontSize: '1.1em', color: '#fff', lineHeight: '1.3' }}>
          {promo.title}
        </h3>
        <p style={{ fontSize: '0.9em', color: 'var(--text-muted)', margin: '0 0 10px 0' }}>
          {promo.description}
        </p>
        
        {promo.discount_value && (
          <div className="discount-tag">{promo.discount_value}</div>
        )}

        {promo.promo_code ? (
          <div className="promo-code-container">
            <span>{promo.promo_code}</span>
            <button className="btn-copy" onClick={() => handleCopy(promo.promo_code)}>Copy</button>
          </div>
        ) : (
          <div style={{ fontSize: '0.8em', color: 'var(--text-muted)', marginTop: '15px' }}>
            *Tidak memerlukan kode promo
          </div>
        )}

        {promo.terms_and_conditions && (
          <div style={{ marginTop: '10px', fontSize: '0.8em', color: 'var(--text-muted)', borderTop: '1px solid var(--border)', paddingTop: '8px' }}>
            <strong>S&K:</strong> {promo.terms_and_conditions}
          </div>
        )}
      </div>
      <div className="card-footer">
        <span style={{ color: 'var(--text-muted)' }}>{detailRoute}</span>
        {promo.source_url && (
          <a href={promo.source_url} target="_blank" rel="noopener noreferrer" className="btn-link">
            Lihat Sumber ➔
          </a>
        )}
      </div>
    </div>
  );
}
