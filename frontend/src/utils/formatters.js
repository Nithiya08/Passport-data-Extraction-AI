/**
 * Formatting and utility helpers for Passport AI Extractor (White & Orange Theme).
 */

export function formatDate(dateStr) {
  if (!dateStr || !dateStr.trim()) return 'Not specified';
  const clean = dateStr.trim();
  
  // Try YYYY-MM-DD
  const parts = clean.split('-');
  if (parts.length === 3) {
    const year = parseInt(parts[0], 10);
    const month = parseInt(parts[1], 10) - 1;
    const day = parseInt(parts[2], 10);
    const d = new Date(year, month, day);
    if (!isNaN(d.getTime())) {
      return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    }
  }

  // Try YYYY-MM
  if (parts.length === 2) {
    return `${clean} (Month/Year)`;
  }

  return clean;
}

export function getConfidenceBadge(confidence) {
  const conf = (confidence || 'high').toLowerCase();
  if (conf === 'high') {
    return {
      label: 'High Confidence',
      badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200'
    };
  }
  if (conf === 'medium') {
    return {
      label: 'Medium Confidence',
      badgeClass: 'bg-amber-50 text-amber-700 border-amber-200'
    };
  }
  return {
    label: 'Low / Review Needed',
    badgeClass: 'bg-rose-50 text-rose-700 border-rose-200'
  };
}

export function getPassportStatusBadge(status, daysUntilExpiry) {
  const st = (status || 'unknown').toLowerCase();
  if (st === 'valid') {
    return {
      label: `Valid (${daysUntilExpiry} days left)`,
      badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      dotClass: 'bg-emerald-500'
    };
  }
  if (st === 'expiring_soon') {
    return {
      label: `Expiring Soon (${daysUntilExpiry} days left)`,
      badgeClass: 'bg-orange-50 text-orange-700 border-orange-200',
      dotClass: 'bg-orange-500 animate-pulse'
    };
  }
  if (st === 'expired') {
    return {
      label: `Expired (${Math.abs(daysUntilExpiry || 0)} days ago)`,
      badgeClass: 'bg-rose-50 text-rose-700 border-rose-200',
      dotClass: 'bg-rose-500'
    };
  }
  return {
    label: 'Status Unknown',
    badgeClass: 'bg-slate-100 text-slate-700 border-slate-200',
    dotClass: 'bg-slate-400'
  };
}

export function formatEventType(type) {
  switch (type) {
    case 'visa':
      return 'Visa Sticker';
    case 'entry_stamp':
      return 'Entry Stamp';
    case 'exit_stamp':
      return 'Exit Stamp';
    case 'residence_permit':
      return 'Residence Permit';
    default:
      return 'Travel Record';
  }
}
