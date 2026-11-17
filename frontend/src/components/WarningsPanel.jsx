import React, { useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react';

export default function WarningsPanel({ warnings }) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  if (!warnings || warnings.length === 0) return null;

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 sm:p-6 text-amber-900 shadow-xs">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-amber-100 border border-amber-200 flex items-center justify-center text-amber-600 flex-shrink-0">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-amber-950 tracking-tight flex items-center gap-2">
              Extraction Warnings & Ambiguities ({warnings.length})
            </h3>
            <p className="text-xs text-amber-800">
              The AI model or forensic rules identified the following fields requiring human verification:
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-1.5 rounded-lg text-amber-700 hover:text-amber-950 hover:bg-amber-100 transition"
        >
          {isCollapsed ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        </button>
      </div>

      {!isCollapsed && (
        <ul className="mt-4 space-y-2 border-t border-amber-200/80 pt-3">
          {warnings.map((warn, idx) => (
            <li key={idx} className="flex items-start gap-2 text-xs text-amber-900 leading-relaxed font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-600 mt-1.5 flex-shrink-0" />
              <span>{warn}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
