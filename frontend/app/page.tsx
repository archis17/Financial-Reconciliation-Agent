'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  TrendingUp,
  Download,
  Sparkles,
  ArrowRight,
  Loader2
} from 'lucide-react';
import axios from 'axios';
import ReconciliationResults from '@/components/ReconciliationResults';
import ProgressIndicator from '@/components/ProgressIndicator';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type Step = 'upload' | 'processing' | 'results';

export default function Home() {
  const [step, setStep] = useState<Step>('upload');
  const [bankFile, setBankFile] = useState<File | null>(null);
  const [ledgerFile, setLedgerFile] = useState<File | null>(null);
  const [processing, setProcessing] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const handleFileSelect = (type: 'bank' | 'ledger', file: File | null) => {
    if (type === 'bank') {
      setBankFile(file);
    } else {
      setLedgerFile(file);
    }
  };

  const handleReconcile = async () => {
    if (!bankFile || !ledgerFile) {
      setError('Please upload both bank statement and ledger files');
      return;
    }

    setProcessing(true);
    setError(null);
    setStep('processing');
    setProgress(0);

    try {
      const formData = new FormData();
      formData.append('bank_file', bankFile);
      formData.append('ledger_file', ledgerFile);
      formData.append('amount_tolerance', '5.0');
      formData.append('date_window_days', '7');
      formData.append('min_confidence', '0.6');
      formData.append('enable_llm', 'true');
      formData.append('min_severity_for_tickets', 'low');

      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 500);

      const response = await axios.post(`${API_URL}/api/reconcile`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 300000, // 5 minutes
      });

      clearInterval(progressInterval);
      setProgress(100);
      
      setTimeout(() => {
        setResults(response.data);
        setStep('results');
        setProcessing(false);
      }, 500);

    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'An error occurred during reconciliation');
      setProcessing(false);
      setStep('upload');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Animated background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>

      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-12"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
            className="inline-block mb-4"
          >
            <Sparkles className="w-16 h-16 text-purple-400" />
          </motion.div>
          <h1 className="text-5xl font-bold mb-4">
            <span className="gradient-text">AI Financial Reconciliation</span>
          </h1>
          <p className="text-xl text-gray-300">
            Automated reconciliation with intelligent matching and AI-powered explanations
          </p>
        </motion.div>

        {/* Main Content */}
        <AnimatePresence mode="wait">
          {step === 'upload' && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              <UploadStep
                bankFile={bankFile}
                ledgerFile={ledgerFile}
                onFileSelect={handleFileSelect}
                onReconcile={handleReconcile}
                error={error}
              />
            </motion.div>
          )}

          {step === 'processing' && (
            <motion.div
              key="processing"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.3 }}
            >
              <ProcessingStep progress={progress} />
            </motion.div>
          )}

          {step === 'results' && results && (
            <motion.div
              key="results"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <ReconciliationResults
                results={results}
                reconciliationId={results.reconciliation_id}
                onReset={() => {
                  setStep('upload');
                  setResults(null);
                  setBankFile(null);
                  setLedgerFile(null);
                }}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <style jsx>{`
        @keyframes blob {
          0%, 100% {
            transform: translate(0, 0) scale(1);
          }
          33% {
            transform: translate(30px, -50px) scale(1.1);
          }
          66% {
            transform: translate(-20px, 20px) scale(0.9);
          }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  );
}

function UploadStep({
  bankFile,
  ledgerFile,
  onFileSelect,
  onReconcile,
  error,
}: {
  bankFile: File | null;
  ledgerFile: File | null;
  onFileSelect: (type: 'bank' | 'ledger', file: File | null) => void;
  onReconcile: () => void;
  error: string | null;
}) {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <FileUploadCard
          title="Bank Statement"
          icon={<FileText className="w-8 h-8" />}
          file={bankFile}
          onFileSelect={(file) => onFileSelect('bank', file)}
          acceptedTypes=".csv,.xlsx"
        />
        <FileUploadCard
          title="Internal Ledger"
          icon={<FileText className="w-8 h-8" />}
          file={ledgerFile}
          onFileSelect={(file) => onFileSelect('ledger', file)}
          acceptedTypes=".csv,.xlsx"
        />
      </div>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 p-4 bg-red-500/20 border border-red-500/50 rounded-lg text-red-200"
        >
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        </motion.div>
      )}

      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onReconcile}
        disabled={!bankFile || !ledgerFile}
        className="w-full py-4 px-8 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-xl font-semibold text-lg shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        <span>Start Reconciliation</span>
        <ArrowRight className="w-5 h-5" />
      </motion.button>
    </div>
  );
}

function FileUploadCard({
  title,
  icon,
  file,
  onFileSelect,
  acceptedTypes,
}: {
  title: string;
  icon: React.ReactNode;
  file: File | null;
  onFileSelect: (file: File | null) => void;
  acceptedTypes: string;
}) {
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      onFileSelect(files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileSelect(e.target.files[0]);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      className="glass-dark rounded-2xl p-6 border border-white/10"
    >
      <div className="flex items-center gap-3 mb-4 text-white">
        {icon}
        <h3 className="text-xl font-semibold">{title}</h3>
      </div>

      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="border-2 border-dashed border-white/20 rounded-xl p-8 text-center hover:border-purple-400/50 transition-colors cursor-pointer"
      >
        <input
          type="file"
          accept={acceptedTypes}
          onChange={handleFileInput}
          className="hidden"
          id={`file-input-${title}`}
        />
        <label
          htmlFor={`file-input-${title}`}
          className="cursor-pointer block"
        >
          {file ? (
            <motion.div
              initial={{ scale: 0.8 }}
              animate={{ scale: 1 }}
              className="space-y-2"
            >
              <CheckCircle2 className="w-12 h-12 text-green-400 mx-auto" />
              <p className="text-white font-medium">{file.name}</p>
              <p className="text-sm text-gray-400">
                {(file.size / 1024).toFixed(2)} KB
              </p>
            </motion.div>
          ) : (
            <div className="space-y-2">
              <Upload className="w-12 h-12 text-gray-400 mx-auto" />
              <p className="text-white">Drop file here or click to upload</p>
              <p className="text-sm text-gray-400">CSV or XLSX format</p>
            </div>
          )}
        </label>
      </div>

      {file && (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          onClick={() => onFileSelect(null)}
          className="mt-4 text-sm text-red-400 hover:text-red-300"
        >
          Remove file
        </motion.button>
      )}
    </motion.div>
  );
}

function ProcessingStep({ progress }: { progress: number }) {
  return (
    <div className="max-w-2xl mx-auto text-center">
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: "spring", stiffness: 200 }}
        className="mb-8"
      >
        <Loader2 className="w-20 h-20 text-purple-400 mx-auto animate-spin" />
      </motion.div>

      <h2 className="text-3xl font-bold text-white mb-4">
        Processing Reconciliation
      </h2>
      <p className="text-gray-300 mb-8">
        Analyzing transactions, matching records, and detecting discrepancies...
      </p>

      <ProgressIndicator progress={progress} />

      <div className="mt-8 grid grid-cols-3 gap-4">
        {['Ingesting', 'Matching', 'Analyzing'].map((step, i) => (
          <motion.div
            key={step}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.2 }}
            className="glass-dark rounded-lg p-4"
          >
            <div className="text-purple-400 font-semibold mb-2">{step}</div>
            <div className="text-sm text-gray-400">In progress...</div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
