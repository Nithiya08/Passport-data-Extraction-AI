import React from 'react';
import { Binary, CheckCircle2, XCircle, AlertTriangle, ShieldCheck, ShieldAlert, Cpu } from 'lucide-react';

export default function MRZVerificationCard({ mrzValidation }) {
  if (!mrzValidation) {
    return (
      <div className="bg-white border border-slate-200 rounded-2xl p-6 text-slate-500 text-sm shadow-sm">
        No Machine Readable Zone (MRZ) detected on uploaded documents.
      </div>
    );
  }

  const {
    mrz_valid,
    raw_lines = [],
    document_number_check,
    dob_check,
    expiry_check,
    composite_check,
    discrepancies = [],
    repaired_fields = {}
  } = mrzValidation;

  const renderCheckBadge = (label, isOk) => {
    if (isOk === null || isOk === undefined) {
      return (
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 flex items-center justify-between">
          <span className="text-xs text-slate-500 font-medium">{label}</span>
          <span className="text-xs text-slate-400 font-mono">Not Checked</span>
        </div>
      );
    }

    return (
      <div className={`rounded-xl p-3 border flex items-center justify-between ${
        isOk ? 'bg-emerald-50/80 border-emerald-200 text-emerald-800' : 'bg-rose-50/80 border-rose-200 text-rose-800'
      }`}>
        <span className="text-xs font-semibold">{label}</span>
        <div className="flex items-center gap-1.5 text-xs font-bold">
          {isOk ? (
            <>
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>PASS (Valid 7-3-1)</span>
            </>
          ) : (
            <>
              <XCircle className="w-4 h-4 text-rose-600" />
              <span>FAIL (Check Mismatch)</span>
            </>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h3 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Cpu className="w-5 h-5 text-orange-500" />
            ICAO Doc 9303 MRZ Verification
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Cryptographic 7-3-1 modulo-10 algorithmic checksum verification across two 44-character TD3 lines.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {mrz_valid ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-bold tracking-wide">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              ALL CHECKS PASSED
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-rose-50 border border-rose-200 text-rose-700 text-xs font-bold tracking-wide">
              <ShieldAlert className="w-4 h-4 text-rose-600" />
              CHECKSUM MISMATCH
            </span>
          )}
        </div>
      </div>

      {/* Raw MRZ Lines Monospace Box */}
      <div className="bg-slate-900 rounded-xl p-4 sm:p-5 border border-slate-800 mb-6 font-mono-mrz overflow-x-auto shadow-inner">
        <div className="text-[10px] text-orange-400 uppercase tracking-widest mb-2 font-sans font-bold flex items-center gap-1.5">
          <Binary className="w-3.5 h-3.5 text-orange-400" />
          Raw OCR Machine Readable Zone (TD3 Standard)
        </div>
        {raw_lines && raw_lines.length > 0 ? (
          raw_lines.map((line, idx) => (
            <div key={idx} className="text-sm sm:text-base font-bold tracking-widest text-orange-200 select-all py-0.5">
              {line || '<'.repeat(44)}
            </div>
          ))
        ) : (
          <div className="text-xs text-slate-500 italic">No MRZ lines decoded.</div>
        )}
      </div>

      {/* Check Digits Status Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {renderCheckBadge('Passport Number Check', document_number_check)}
        {renderCheckBadge('Date of Birth Check', dob_check)}
        {renderCheckBadge('Expiry Date Check', expiry_check)}
        {renderCheckBadge('Composite Check Digit', composite_check)}
      </div>

      {/* Algorithmic MRZ Repairs Callout */}
      {repaired_fields && Object.keys(repaired_fields).length > 0 && (
        <div className="mt-4 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 shadow-2xs">
          <div className="flex items-center gap-2 font-bold text-xs tracking-wider uppercase mb-1.5 text-emerald-800">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            Algorithmic Character Recovery Active (Damaged Document Repaired)
          </div>
          <ul className="list-disc list-inside space-y-1 text-xs text-emerald-900/90 font-medium">
            {Object.entries(repaired_fields).map(([field, desc], idx) => (
              <li key={idx}>
                <strong className="capitalize">{field.replace('_', ' ')}:</strong> {desc}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Discrepancies Callout */}
      {discrepancies && discrepancies.length > 0 && (
        <div className="mt-5 p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800">
          <div className="flex items-center gap-2 font-bold text-xs tracking-wider uppercase mb-1.5">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            Verification Discrepancies Detected
          </div>
          <ul className="list-disc list-inside space-y-1 text-xs text-amber-900/90">
            {discrepancies.map((disc, idx) => (
              <li key={idx}>{disc}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
