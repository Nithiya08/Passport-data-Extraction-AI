import React from 'react';
import { Globe, Navigation } from 'lucide-react';
import { formatDate } from '../utils/formatters';

export default function TravelSummaryCard({ travelSummary }) {
  if (!travelSummary) return null;

  const {
    total_countries = 0,
    countries_visited = [],
    total_events = 0,
    total_visas = 0,
    total_entry_stamps = 0,
    total_exit_stamps = 0,
    visas_summary = []
  } = travelSummary;

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Navigation className="w-5 h-5 text-orange-500" />
            Travel Intelligence Summary
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Aggregated metrics derived across all detected stamps and visa records.
          </p>
        </div>
      </div>

      {/* 4 Metric Tiles */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-50 border border-slate-200/90 rounded-xl p-4">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
            Countries Visited
          </span>
          <span className="text-2xl font-extrabold text-orange-600 font-mono">{total_countries}</span>
          <span className="text-[10px] text-slate-400 block mt-0.5">Excludes home country</span>
        </div>

        <div className="bg-slate-50 border border-slate-200/90 rounded-xl p-4">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
            Visas Issued
          </span>
          <span className="text-2xl font-extrabold text-amber-600 font-mono">{total_visas}</span>
        </div>

        <div className="bg-slate-50 border border-slate-200/90 rounded-xl p-4">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
            Entry Stamps
          </span>
          <span className="text-2xl font-extrabold text-blue-600 font-mono">{total_entry_stamps}</span>
        </div>

        <div className="bg-slate-50 border border-slate-200/90 rounded-xl p-4">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
            Exit Stamps
          </span>
          <span className="text-2xl font-extrabold text-emerald-600 font-mono">{total_exit_stamps}</span>
        </div>
      </div>

      {/* Countries Visited Tags */}
      {countries_visited.length > 0 && (
        <div className="mb-6">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-2">
            Countries & Territories Visited (Excluding Home Country):
          </span>
          <div className="flex flex-wrap gap-2">
            {countries_visited.map((country, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-orange-50 border border-orange-200 text-xs font-semibold text-orange-800 shadow-2xs"
              >
                <Globe className="w-3.5 h-3.5 text-orange-500" />
                {country}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Visas Breakdown Table */}
      {visas_summary.length > 0 && (
        <div className="pt-5 border-t border-slate-100">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-3">
            Visa Documents & Validity Ranges:
          </span>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-slate-600 uppercase text-[10px] tracking-wider font-bold border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-3">Country / Territory</th>
                  <th className="py-2.5 px-3">Visa Type</th>
                  <th className="py-2.5 px-3">Visa Serial</th>
                  <th className="py-2.5 px-3">Valid From</th>
                  <th className="py-2.5 px-3">Valid Until</th>
                  <th className="py-2.5 px-3">Stay Duration</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {visas_summary.map((v, i) => (
                  <tr key={i} className="hover:bg-slate-50/70">
                    <td className="py-2.5 px-3 font-bold text-slate-900">{v.country || 'N/A'}</td>
                    <td className="py-2.5 px-3">{v.visa_type || 'Standard'}</td>
                    <td className="py-2.5 px-3 font-mono font-bold text-orange-600">{v.visa_number || 'N/A'}</td>
                    <td className="py-2.5 px-3">{formatDate(v.valid_from)}</td>
                    <td className="py-2.5 px-3">{formatDate(v.valid_until)}</td>
                    <td className="py-2.5 px-3 font-medium text-slate-800">{v.duration_of_stay || 'Standard'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
