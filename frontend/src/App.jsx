import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import FileUpload from './components/FileUpload';
import PersonalDetailsCard from './components/PersonalDetailsCard';
import MRZVerificationCard from './components/MRZVerificationCard';
import TravelTimeline from './components/TravelTimeline';
import TravelSummaryCard from './components/TravelSummaryCard';
import WarningsPanel from './components/WarningsPanel';
import ExportActions from './components/ExportActions';
import { checkServerHealth, extractPassportDocuments } from './api/client';
import { AlertCircle, ShieldCheck, Zap, RefreshCw } from 'lucide-react';

export default function App() {
  const [files, setFiles] = useState([]);
  const [serverStatus, setServerStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [progressText, setProgressText] = useState('');
  const [progressPercent, setProgressPercent] = useState(0);
  const [errorMsg, setErrorMsg] = useState('');
  const [extractionData, setExtractionData] = useState(null);

  // Check health on mount
  useEffect(() => {
    checkServerHealth().then(status => {
      setServerStatus(status);
    });
  }, []);

  const handleExtract = async (forceRefresh = false) => {
    if (files.length === 0) return;

    setIsLoading(true);
    setErrorMsg('');
    setProgressPercent(15);
    setProgressText(forceRefresh ? 'Forcing fresh re-extraction from Gemini...' : 'Checking in-memory cache & processing document...');

    // Progress milestone simulations for smooth UX
    const timer1 = setTimeout(() => {
      setProgressPercent(40);
      setProgressText('PyMuPDF converting pages & optimizing resolution...');
    }, 1200);

    const timer2 = setTimeout(() => {
      setProgressPercent(70);
      setProgressText('Gemini extracting biodata & detecting stamps...');
    }, 2800);

    const timer3 = setTimeout(() => {
      setProgressPercent(90);
      setProgressText('ICAO 9303 verifying MRZ check digits & ordering timeline...');
    }, 4500);

    try {
      const result = await extractPassportDocuments(files, (percent) => {
        if (percent < 50) setProgressPercent(percent);
      }, forceRefresh);

      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);

      setProgressPercent(100);
      setProgressText(result.is_cached ? 'Instant cache hit!' : 'Extraction complete!');
      setExtractionData(result);
    } catch (err) {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      setErrorMsg(err.message || 'An error occurred during extraction.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartOver = () => {
    setFiles([]);
    setExtractionData(null);
    setErrorMsg('');
  };

  return (
    <div className="min-h-screen bg-slate-50/80 text-slate-900 flex flex-col antialiased selection:bg-orange-500 selection:text-white">
      {/* Navigation Header */}
      <Navbar
        serverStatus={serverStatus}
        hasData={!!extractionData}
        onClearData={handleStartOver}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Error Banner */}
        {errorMsg && (
          <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 flex items-start gap-3 text-rose-800 text-sm shadow-sm no-print">
            <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-600 mt-0.5" />
            <div className="flex-1">
              <h4 className="font-semibold text-rose-900">Extraction Error</h4>
              <p className="mt-0.5">{errorMsg}</p>
            </div>
            <button
              onClick={() => setErrorMsg('')}
              className="text-xs text-rose-700 hover:text-rose-900 font-semibold underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* View 1: Upload Stage */}
        {!extractionData && (
          <div className="max-w-4xl mx-auto space-y-8">
            <div className="text-center space-y-3 pt-4 sm:pt-8">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-orange-100/80 text-orange-700 border border-orange-200 shadow-sm">
                <ShieldCheck className="w-4 h-4 text-orange-600" />
                AI-Powered Forensic Passport OCR
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
                Extract Passport Biodata & Travel Timeline
              </h2>
              <p className="text-sm sm:text-base text-slate-600 max-w-2xl mx-auto">
                Upload your passport biodata page, visa stickers, and stamp pages. Our engine decodes TD3 MRZ check digits and reconstructs a chronological travel history using Google Gemini.
              </p>
            </div>

            <FileUpload
              files={files}
              setFiles={setFiles}
              onExtract={handleExtract}
              isLoading={isLoading}
              progressText={progressText}
              progressPercent={progressPercent}
            />
          </div>
        )}

        {/* View 2: Extraction Results Stage */}
        {extractionData && (
          <div className="space-y-8 animate-fade-in">
            {/* Cache Hit Notification Banner */}
            {extractionData.is_cached && (
              <div className="p-3.5 sm:p-4 rounded-2xl bg-amber-50 border border-amber-200/90 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-amber-900 text-xs shadow-2xs no-print">
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-amber-500/10 border border-amber-300 flex items-center justify-center flex-shrink-0 text-amber-600">
                    <Zap className="w-4 h-4 fill-amber-500 text-amber-600" />
                  </div>
                  <div>
                    <span className="font-bold text-amber-950">Served from In-Memory Cache (0.02s):</span>
                    <span className="text-amber-800 ml-1">Identical document detected. Cached results returned with zero API token consumption.</span>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => handleExtract(true)}
                  className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-xl bg-white hover:bg-amber-100 border border-amber-300 text-amber-900 text-xs font-semibold transition shadow-2xs flex-shrink-0"
                  title="Bypass memory cache and re-call Gemini"
                >
                  <RefreshCw className="w-3.5 h-3.5 text-amber-600" />
                  <span>Re-extract with Gemini</span>
                </button>
              </div>
            )}

            {/* Warnings Alert Panel */}
            {extractionData.warnings && extractionData.warnings.length > 0 && (
              <WarningsPanel warnings={extractionData.warnings} />
            )}

            {/* Holder Header & Personal Details Grid */}
            <PersonalDetailsCard
              personalDetails={extractionData.personal_details}
              passportStatus={extractionData.passport_status}
              daysUntilExpiry={extractionData.days_until_expiry}
            />

            {/* ICAO Doc 9303 MRZ Verification Card */}
            <MRZVerificationCard
              mrzValidation={extractionData.mrz_validation}
            />

            {/* Travel Summary Metrics */}
            <TravelSummaryCard
              travelSummary={extractionData.travel_summary}
            />

            {/* Chronological Travel Timeline */}
            <TravelTimeline
              travelEvents={extractionData.travel_events}
            />

            {/* Export & Actions Footer */}
            <ExportActions
              extractionData={extractionData}
              onStartOver={handleStartOver}
            />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500 no-print">
        <p>
          Passport AI Extractor • Built with FastAPI, Pydantic v2, PyMuPDF, and Google Gemini • Human verification recommended for all travel records.
        </p>
      </footer>
    </div>
  );
}
