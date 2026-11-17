import React, { useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, X, Sparkles, AlertCircle } from 'lucide-react';

export default function FileUpload({ files, setFiles, onExtract, isLoading, progressText, progressPercent }) {
  const [errorMsg, setErrorMsg] = useState('');
  const [previews, setPreviews] = useState([]);

  // Generate previews for image files
  useEffect(() => {
    const urls = files.map(file => {
      if (file.type.startsWith('image/')) {
        return { name: file.name, url: URL.createObjectURL(file), isImage: true, size: file.size };
      }
      return { name: file.name, isImage: false, size: file.size };
    });
    setPreviews(urls);

    return () => {
      urls.forEach(p => {
        if (p.url) URL.revokeObjectURL(p.url);
      });
    };
  }, [files]);

  const onDrop = (acceptedFiles, rejectedFiles) => {
    setErrorMsg('');

    if (rejectedFiles && rejectedFiles.length > 0) {
      const first = rejectedFiles[0];
      if (first.errors.some(e => e.code === 'file-invalid-type')) {
        setErrorMsg('Invalid file format. Please upload JPG, PNG, WEBP, or PDF.');
      } else {
        setErrorMsg(first.errors[0]?.message || 'File upload rejected.');
      }
      return;
    }

    setFiles(prev => [...prev, ...acceptedFiles]);
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const loadSpecimenDocuments = async () => {
    setErrorMsg('');
    try {
      const specimens = [
        { path: '/samples/specimen_passport_bio.png', name: 'specimen_passport_bio.png', type: 'image/png' },
        { path: '/samples/specimen_visas_page.png', name: 'specimen_visas_page.png', type: 'image/png' },
        { path: '/samples/specimen_stamps_page.png', name: 'specimen_stamps_page.png', type: 'image/png' },
      ];

      const loadedFiles = await Promise.all(
        specimens.map(async (s) => {
          const res = await fetch(s.path);
          const blob = await res.blob();
          return new File([blob], s.name, { type: s.type });
        })
      );

      setFiles(loadedFiles);
    } catch (err) {
      setErrorMsg('Failed to load specimen sample documents. Please upload manually.');
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/webp': ['.webp'],
      'application/pdf': ['.pdf'],
    },
    multiple: true,
    disabled: isLoading,
  });

  return (
    <div className="bg-white border border-slate-200/90 rounded-2xl p-6 sm:p-8 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <UploadCloud className="w-6 h-6 text-orange-500" />
            Upload Passport Documents
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Upload the passport photo/biodata page, visa stickers, and entry/exit stamp pages (JPG, PNG, WEBP, or PDF).
          </p>
        </div>

        <button
          type="button"
          onClick={loadSpecimenDocuments}
          disabled={isLoading}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-orange-50 hover:bg-orange-100 border border-orange-200 text-orange-700 text-xs font-semibold tracking-wide transition shadow-sm"
        >
          <Sparkles className="w-4 h-4 text-orange-500" />
          Load Specimen Sample
        </button>
      </div>

      {errorMsg && (
        <div className="mb-5 p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3 text-rose-800 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-600 mt-0.5" />
          <div>
            <p className="font-medium">{errorMsg}</p>
          </div>
        </div>
      )}

      {/* Dropzone Container */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all ${
          isDragActive
            ? 'border-orange-500 bg-orange-50/60 scale-[0.99]'
            : 'border-slate-300 hover:border-orange-400 bg-slate-50/60 hover:bg-orange-50/20'
        }`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center justify-center">
          <div className="w-16 h-16 rounded-2xl bg-orange-100/80 border border-orange-200 flex items-center justify-center text-orange-600 mb-4 shadow-sm">
            <UploadCloud className="w-8 h-8" />
          </div>
          <p className="text-base font-semibold text-slate-800 mb-1">
            {isDragActive ? 'Drop the passport files here...' : 'Drag & drop passport pages or click to browse'}
          </p>
          <p className="text-xs text-slate-500 max-w-md mb-3">
            Supports multi-page PDFs, high-res scans, and photos (no file size limits).
          </p>
          <div className="flex flex-wrap items-center justify-center gap-2">
            <span className="px-2 py-0.5 text-[11px] font-mono font-medium rounded bg-white text-slate-600 border border-slate-200 shadow-2xs">JPEG</span>
            <span className="px-2 py-0.5 text-[11px] font-mono font-medium rounded bg-white text-slate-600 border border-slate-200 shadow-2xs">PNG</span>
            <span className="px-2 py-0.5 text-[11px] font-mono font-medium rounded bg-white text-slate-600 border border-slate-200 shadow-2xs">WEBP</span>
            <span className="px-2 py-0.5 text-[11px] font-mono font-medium rounded bg-white text-slate-600 border border-slate-200 shadow-2xs">PDF</span>
          </div>
        </div>
      </div>

      {/* Uploaded Files Previews Grid */}
      {previews.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Selected Files ({previews.length})
            </h3>
            <button
              onClick={() => setFiles([])}
              disabled={isLoading}
              className="text-xs text-slate-500 hover:text-rose-600 font-medium transition"
            >
              Remove all
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {previews.map((item, idx) => (
              <div
                key={idx}
                className="relative group rounded-xl border border-slate-200 bg-white p-2.5 flex items-center gap-3 overflow-hidden shadow-xs hover:border-orange-300 transition"
              >
                {item.isImage && item.url ? (
                  <div className="w-12 h-12 rounded-lg bg-slate-100 overflow-hidden flex-shrink-0 border border-slate-200">
                    <img src={item.url} alt={item.name} className="w-full h-full object-cover" />
                  </div>
                ) : (
                  <div className="w-12 h-12 rounded-lg bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center flex-shrink-0 font-bold text-xs">
                    PDF
                  </div>
                )}

                <div className="flex-1 min-w-0 pr-6">
                  <p className="text-xs font-semibold text-slate-800 truncate">{item.name}</p>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    {(item.size / (1024 * 1024)).toFixed(2)} MB • Page {idx + 1}
                  </p>
                </div>

                {!isLoading && (
                  <button
                    type="button"
                    onClick={() => removeFile(idx)}
                    className="absolute top-2 right-2 p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition"
                    title="Remove file"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Extract CTA & Progress Display */}
      <div className="mt-8 flex flex-col items-center">
        {isLoading ? (
          <div className="w-full max-w-md bg-slate-50 border border-slate-200 rounded-2xl p-5 text-center shadow-xs">
            <div className="flex items-center justify-center gap-3 mb-3">
              <div className="w-5 h-5 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
              <span className="text-sm font-semibold text-slate-800 tracking-wide">Processing Document Set</span>
            </div>
            <p className="text-xs text-orange-600 font-semibold mb-3">{progressText || 'Extracting forensic passport details...'}</p>
            <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-gradient-to-r from-orange-500 to-amber-500 h-full rounded-full transition-all duration-300"
                style={{ width: `${progressPercent || 35}%` }}
              />
            </div>
          </div>
        ) : (
          <button
            type="button"
            onClick={onExtract}
            disabled={files.length === 0}
            className={`w-full sm:w-auto px-8 py-3.5 rounded-xl font-semibold text-sm tracking-wide transition-all shadow-md flex items-center justify-center gap-2.5 ${
              files.length > 0
                ? 'bg-orange-600 hover:bg-orange-500 text-white shadow-orange-500/20 active:scale-[0.98]'
                : 'bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            Extract Details ({files.length} {files.length === 1 ? 'file' : 'files'})
          </button>
        )}
      </div>
    </div>
  );
}
