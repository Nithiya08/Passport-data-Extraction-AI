import React from 'react';
import { User, Shield, Calendar, Globe, Award, MapPin, Hash, Users, Home, CheckCircle2 } from 'lucide-react';
import { formatDate, getPassportStatusBadge } from '../utils/formatters';

export default function PersonalDetailsCard({ personalDetails, passportStatus, daysUntilExpiry }) {
  if (!personalDetails) return null;

  const statusBadge = getPassportStatusBadge(passportStatus, daysUntilExpiry);

  const renderValue = (field, label, icon) => {
    const val = personalDetails[field];
    return (
      <div className="bg-slate-50/80 border border-slate-200/90 rounded-xl p-3.5 flex flex-col justify-between">
        <span className="text-[11px] font-semibold tracking-wider uppercase text-slate-500 flex items-center gap-1.5 mb-1.5">
          {icon}
          {label}
        </span>
        <span className={`text-sm font-semibold ${val ? 'text-slate-900' : 'text-slate-400 italic font-normal'}`}>
          {val || 'Not found'}
        </span>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* 1. Executive Summary Header Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm relative overflow-hidden">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-center gap-5">
            {/* Photo Avatar Placeholder */}
            <div className="w-20 h-24 rounded-xl bg-slate-100 border-2 border-slate-200 flex flex-col items-center justify-center text-slate-400 overflow-hidden shadow-inner flex-shrink-0">
              <User className="w-10 h-10 text-slate-400 mb-1" />
              <span className="text-[9px] font-mono tracking-widest uppercase text-slate-400 font-bold">PHOTO</span>
            </div>

            <div>
              <div className="flex flex-wrap items-center gap-3">
                <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
                  {personalDetails.full_name || `${personalDetails.given_names || ''} ${personalDetails.surname || ''}`.trim() || 'Passport Holder'}
                </h2>
                <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${statusBadge.badgeClass}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${statusBadge.dotClass}`} />
                  {statusBadge.label}
                </span>
              </div>

              <div className="flex flex-wrap items-center gap-y-1 gap-x-4 mt-2 text-xs text-slate-600">
                <span className="flex items-center gap-1">
                  <Globe className="w-3.5 h-3.5 text-orange-500" />
                  <strong className="text-slate-800 font-semibold">{personalDetails.nationality || 'Nationality Unspecified'}</strong>
                  {personalDetails.issuing_country_code && (
                    <span className="px-1.5 py-0.2 rounded bg-orange-100 text-[10px] font-mono font-bold text-orange-700 border border-orange-200">
                      {personalDetails.issuing_country_code}
                    </span>
                  )}
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Hash className="w-3.5 h-3.5 text-orange-500" />
                  Passport No: <strong className="text-slate-800 font-mono font-semibold">{personalDetails.passport_number || 'N/A'}</strong>
                </span>
                <span>•</span>
                <span>
                  Sex: <strong className="text-slate-800 font-semibold">{personalDetails.sex || 'Unspecified'}</strong>
                </span>
              </div>
            </div>
          </div>

          {/* Tamper-Proof Verification Badge */}
          <div className="no-print">
            <div className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 text-xs font-semibold shadow-2xs">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Verified Document Record</span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Structured Personal Details Grid Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Shield className="w-5 h-5 text-orange-500" />
            Biodata & Personal Details
          </h3>
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">ICAO Doc 9303 Compliant</span>
        </div>

        {/* Primary Identification Fields */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {renderValue('passport_number', 'Passport Number', <Hash className="w-3.5 h-3.5 text-orange-500" />)}
          {renderValue('surname', 'Surname / Primary Name', <User className="w-3.5 h-3.5 text-orange-500" />)}
          {renderValue('given_names', 'Given Names', <User className="w-3.5 h-3.5 text-orange-500" />)}
          {renderValue('nationality', 'Nationality', <Globe className="w-3.5 h-3.5 text-orange-500" />)}
          {renderValue('date_of_birth', 'Date of Birth', <Calendar className="w-3.5 h-3.5 text-orange-500" />)}
          {renderValue('place_of_birth', 'Place of Birth', <MapPin className="w-3.5 h-3.5 text-orange-500" />)}
          {renderValue('sex', 'Sex / Gender', <User className="w-3.5 h-3.5 text-orange-500" />)}
          {renderValue('personal_number', 'Personal / National ID', <Hash className="w-3.5 h-3.5 text-orange-500" />)}
          {renderValue('date_of_issue', 'Date of Issue', <Calendar className="w-3.5 h-3.5 text-emerald-600" />)}
          {renderValue('date_of_expiry', 'Date of Expiry', <Calendar className="w-3.5 h-3.5 text-rose-600" />)}
          {renderValue('issuing_authority', 'Issuing Authority', <Award className="w-3.5 h-3.5 text-emerald-600" />)}
          {renderValue('issuing_country', 'Issuing Country', <Globe className="w-3.5 h-3.5 text-emerald-600" />)}
        </div>

        {/* Extended Family & Address Information */}
        <div className="mt-8 pt-6 border-t border-slate-100">
          <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Users className="w-4 h-4 text-orange-500" />
            Extended Endorsements & Observation Details (if present)
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {renderValue('father_name', 'Father / Legal Guardian', <Users className="w-3.5 h-3.5 text-slate-400" />)}
            {renderValue('mother_name', 'Mother Name', <Users className="w-3.5 h-3.5 text-slate-400" />)}
            {renderValue('spouse_name', 'Spouse Name', <Users className="w-3.5 h-3.5 text-slate-400" />)}
            {renderValue('old_passport_details', 'Old Passport File No / Details', <Hash className="w-3.5 h-3.5 text-slate-400" />)}
            <div className="sm:col-span-2">
              {renderValue('address', 'Permanent Address', <Home className="w-3.5 h-3.5 text-slate-400" />)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
