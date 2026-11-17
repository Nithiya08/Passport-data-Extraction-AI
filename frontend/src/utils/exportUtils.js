/**
 * Export helpers: JSON download, CSV generator, Print view.
 */

export function downloadJSON(data, filename = 'passport_extracted_data.json') {
  const jsonStr = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonStr], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function downloadTimelineCSV(events, filename = 'passport_travel_timeline.csv') {
  if (!events || events.length === 0) return;

  const headers = [
    'Date',
    'Event Type',
    'Country',
    'Port / City',
    'Visa Type',
    'Visa Number',
    'Entries Allowed',
    'Stay Permitted',
    'Days Stayed (Between Entry & Exit)',
    'Page',
    'Confidence',
    'Notes'
  ];

  const escapeCSV = (val) => {
    if (val === null || val === undefined) return '""';
    const str = String(val).replace(/"/g, '""');
    return `"${str}"`;
  };

  const rows = events.map(e => [
    escapeCSV(e.date || 'Undated'),
    escapeCSV(e.event_type),
    escapeCSV(e.country || 'Unknown'),
    escapeCSV(e.city_or_port || ''),
    escapeCSV(e.visa_type || ''),
    escapeCSV(e.visa_number || ''),
    escapeCSV(e.number_of_entries || ''),
    escapeCSV(e.duration_of_stay || ''),
    escapeCSV(e.days_stayed !== undefined && e.days_stayed !== null ? `${e.days_stayed} days` : ''),
    escapeCSV(e.source_page || ''),
    escapeCSV(e.confidence || 'high'),
    escapeCSV(e.notes || '')
  ]);

  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.join(','))
  ].join('\r\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function printExecutiveReport() {
  window.print();
}

