import React, { useState } from 'react';
import {
  Calendar,
  PlaneLanding,
  PlaneTakeoff,
  FileCheck,
  Building,
  Compass,
  ArrowUpDown,
  Filter,
  Clock,
  MapPin,
  Tag,
  AlertCircle
} from 'lucide-react';
import { formatDate, getConfidenceBadge, formatEventType } from '../utils/formatters';

export default function TravelTimeline({ travelEvents = [] }) {
  const [sortOrder, setSortOrder] = useState('asc'); // 'asc' = oldest first (default), 'desc' = newest first
  const [filterType, setFilterType] = useState('all');

  // Guarantee travelEvents is always a valid array
  const safeEvents = Array.isArray(travelEvents) ? travelEvents : [];

  // Filter events
  const filteredEvents = safeEvents.filter(e => {
    if (filterType === 'all') return true;
    return e.event_type === filterType;
  });

  // Sort events
  const sortedEvents = [...filteredEvents].sort((a, b) => {
    const dateA = a.date || '9999-99-99';
    const dateB = b.date || '9999-99-99';
    if (sortOrder === 'asc') {
      return dateA.localeCompare(dateB);
    } else {
      return dateB.localeCompare(dateA);
    }
  });

  const getEventIcon = (type) => {
    switch (type) {
      case 'entry_stamp':
        return <PlaneLanding className="w-4 h-4 text-blue-600" />;
      case 'exit_stamp':
        return <PlaneTakeoff className="w-4 h-4 text-emerald-600" />;
      case 'visa':
        return <FileCheck className="w-4 h-4 text-orange-600" />;
      case 'residence_permit':
        return <Building className="w-4 h-4 text-purple-600" />;
      default:
        return <Compass className="w-4 h-4 text-slate-600" />;
    }
  };

  const getEventBadgeColor = (type) => {
    switch (type) {
      case 'entry_stamp':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'exit_stamp':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'visa':
        return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'residence_permit':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h3 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Clock className="w-5 h-5 text-orange-500" />
            Chronological Travel Timeline
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Audit-ready chronological sequence of verified visas, border entries, and exits.
          </p>
        </div>

        {/* Controls: Sort Toggle */}
        <div className="flex items-center gap-2 no-print">
          <button
            type="button"
            onClick={() => setSortOrder(prev => (prev === 'asc' ? 'desc' : 'asc'))}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 text-xs font-semibold transition shadow-2xs"
          >
            <ArrowUpDown className="w-3.5 h-3.5 text-orange-500" />
            <span>{sortOrder === 'asc' ? 'Oldest First' : 'Newest First'}</span>
          </button>
        </div>
      </div>

      {/* Filter Chips */}
      <div className="flex flex-wrap items-center gap-2 mb-8 no-print">
        <span className="text-xs font-bold text-slate-500 mr-1 flex items-center gap-1">
          <Filter className="w-3.5 h-3.5" />
          Filter:
        </span>
        {[
          { id: 'all', label: `All (${safeEvents.length})` },
          { id: 'entry_stamp', label: 'Entries' },
          { id: 'exit_stamp', label: 'Exits' },
          { id: 'visa', label: 'Visas' },
          { id: 'residence_permit', label: 'Permits' },
        ].map(chip => (
          <button
            key={chip.id}
            type="button"
            onClick={() => setFilterType(chip.id)}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
              filterType === chip.id
                ? 'bg-orange-600 text-white shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:text-slate-900 hover:bg-slate-200'
            }`}
          >
            {chip.label}
          </button>
        ))}
      </div>

      {/* Timeline Stream */}
      {sortedEvents.length === 0 ? (
        <div className="text-center py-12 text-slate-400 text-sm">
          No travel events matching the selected filter.
        </div>
      ) : (
        <div className="relative pl-6 sm:pl-8 border-l-2 border-orange-200 space-y-6">
          {sortedEvents.map((evt, idx) => {
            const conf = getConfidenceBadge(evt.confidence);

            return (
              <div key={evt.id || idx} className="relative group">
                {/* Connecting Node Icon */}
                <div className="absolute -left-[35px] sm:-left-[43px] top-1.5 w-8 h-8 rounded-full bg-white border-2 border-orange-500 flex items-center justify-center group-hover:scale-110 transition shadow-sm">
                  {getEventIcon(evt.event_type)}
                </div>

                {/* Event Card */}
                <div className="bg-white border border-slate-200/90 rounded-2xl p-5 hover:border-orange-300 hover:shadow-xs transition">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getEventBadgeColor(evt.event_type)}`}>
                        {formatEventType(evt.event_type)}
                      </span>
                      <h4 className="text-base font-bold text-slate-900 tracking-tight">
                        {evt.country || 'Unknown Country'}
                      </h4>
                      {evt.city_or_port && (
                        <span className="text-xs text-slate-500 flex items-center gap-1 font-medium">
                          <MapPin className="w-3 h-3 text-slate-400" />
                          {evt.city_or_port}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded-md text-[11px] font-bold border ${conf.badgeClass}`}>
                        {conf.label}
                      </span>
                    </div>
                  </div>

                  {/* Main Event Data Row */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs text-slate-700 my-2">
                    <div className="flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-orange-500" />
                      <span>Date:</span>
                      <strong className="text-slate-900 font-mono font-bold">{formatDate(evt.date)}</strong>
                    </div>

                    {evt.source_page && (
                      <div className="flex items-center gap-1.5 text-slate-500">
                        <Tag className="w-3.5 h-3.5 text-orange-500" />
                        <span>Source:</span>
                        <strong className="text-slate-800">Page {evt.source_page}</strong>
                      </div>
                    )}

                    {/* Stay Duration between Entry & Exit */}
                    {evt.days_stayed !== undefined && evt.days_stayed !== null && (
                      <div className="sm:col-span-2">
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold shadow-2xs">
                          <Clock className="w-3.5 h-3.5 text-emerald-600" />
                          Duration of Stay: {evt.days_stayed} {evt.days_stayed === 1 ? 'day' : 'days'}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Visa Details (if type === 'visa') */}
                  {evt.event_type === 'visa' && (
                    <div className="mt-3 p-3 rounded-xl bg-orange-50/50 border border-orange-100 text-xs grid grid-cols-2 sm:grid-cols-4 gap-2 text-slate-700">
                      {evt.visa_type && (
                        <div>
                          <span className="text-[10px] uppercase text-slate-500 font-bold block">Category</span>
                          <span className="font-semibold text-slate-900">{evt.visa_type}</span>
                        </div>
                      )}
                      {evt.visa_number && (
                        <div>
                          <span className="text-[10px] uppercase text-slate-500 font-bold block">Visa Number</span>
                          <span className="font-mono font-bold text-orange-700">{evt.visa_number}</span>
                        </div>
                      )}
                      {(evt.valid_from || evt.valid_until) && (
                        <div>
                          <span className="text-[10px] uppercase text-slate-500 font-bold block">Validity Range</span>
                          <span className="font-semibold text-slate-900">
                            {formatDate(evt.valid_from)} - {formatDate(evt.valid_until)}
                          </span>
                        </div>
                      )}
                      {evt.duration_of_stay && (
                        <div>
                          <span className="text-[10px] uppercase text-slate-500 font-bold block">Allowed Stay</span>
                          <span className="font-semibold text-slate-900">{evt.duration_of_stay}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Forensic Observation Notes */}
                  {evt.notes && (
                    <div className="mt-2.5 text-xs text-slate-500 flex items-start gap-1.5 italic">
                      <AlertCircle className="w-3.5 h-3.5 text-amber-500 flex-shrink-0 mt-0.5" />
                      <span>{evt.notes}</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
