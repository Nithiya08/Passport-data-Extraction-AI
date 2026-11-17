import React from 'react';
import { Download, FileSpreadsheet, Printer, RotateCcw, Lock } from 'lucide-react';
import { downloadJSON, downloadTimelineCSV, printExecutiveReport } from '../utils/exportUtils';

export default function ExportActions({ extractionData, onStartOver }) {
  const handleDownloadJSON = () => {
    downloadJSON(extractionData, `passport_${extractionData.personal_details?.passport_number || 'data'}.json`);
  };

  const handleDownloadCSV = () => {
    downloadTimelineCSV(extractionData.travel_events, `passport_timeline_${extractionData.personal_details?.passport_number || 'export'}.csv`);
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm no-print">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div>
          <h3 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Download className="w-5 h-5 text-orange-500" />
            Export & Verification Report
          </h3>
          <p className="text-xs text-slate-500 mt-1 max-w-xl">
            Export the verified passport metadata and chronological travel sequence as structured JSON, spreadsheet CSV, or printable executive PDF report.
          </p>
        </div>

        {/* Buttons Action Group */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleDownloadJSON}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 text-xs font-semibold shadow-2xs transition"
          >
            <Download className="w-4 h-4 text-orange-500" />
            Download JSON
          </button>

          <button
            type="button"
            onClick={handleDownloadCSV}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 text-xs font-semibold shadow-2xs transition"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
            Download CSV (Timeline)
          </button>

          <button
            type="button"
            onClick={printExecutiveReport}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-orange-600 hover:bg-orange-500 text-white text-xs font-semibold shadow-md shadow-orange-500/20 transition"
          >
            <Printer className="w-4 h-4" />
            Print / Save as PDF
          </button>

          <button
            type="button"
            onClick={onStartOver}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 text-xs font-semibold transition shadow-2xs"
          >
            <RotateCcw className="w-4 h-4" />
            Clear & New Upload
          </button>
        </div>
      </div>

      {/* Privacy Notice Banner */}
      <div className="mt-6 pt-5 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
        <div className="flex items-center gap-2">
          <Lock className="w-4 h-4 text-emerald-600" />
          <span>
            <strong className="text-slate-700">Privacy Guarantee:</strong> All document pages are processed strictly in-memory and discarded upon completion. No personal data or images are written to disk.
          </span>
        </div>
      </div>
    </div>
  );
}
