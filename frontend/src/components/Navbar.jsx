import React from 'react';
import { ShieldCheck, Lock, Trash2 } from 'lucide-react';

export default function Navbar({ serverStatus, hasData, onClearData }) {
  return (
    <header className="border-b border-slate-200 bg-white/90 backdrop-blur sticky top-0 z-40 shadow-sm no-print">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-orange-500 to-amber-500 flex items-center justify-center shadow-md shadow-orange-500/20 text-white font-bold">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-slate-900 tracking-tight">Passport AI Extractor</h1>
              <span className="text-[10px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full bg-orange-100 text-orange-700 border border-orange-200">
                PROD v1.0
              </span>
            </div>
            <p className="text-xs text-slate-500 hidden sm:block">Forensic OCR, TD3 MRZ Verification & Chronological Travel Timeline</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Privacy Badge */}
          <div className="hidden md:flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-medium">
            <Lock className="w-3.5 h-3.5" />
            <span>In-Memory Only • Zero Storage</span>
          </div>

          {/* Server / Gemini Status Indicator */}
          <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-100 border border-slate-200 text-xs text-slate-700">
            <span className={`w-2 h-2 rounded-full ${serverStatus?.status === 'ok' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
            <span className="font-mono text-[11px] font-semibold">{serverStatus?.gemini_model || 'gemini-3.5-flash'}</span>
          </div>

          {/* Clear Data Button */}
          {hasData && (
            <button
              onClick={onClearData}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 text-xs font-semibold transition"
              title="Clear all extracted data and start over"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Start Over</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
