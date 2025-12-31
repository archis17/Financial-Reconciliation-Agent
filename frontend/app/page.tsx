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
  ArrowRight,
  Loader2,
  LogOut,
  User
} from 'lucide-react';
import axios from 'axios';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import ReconciliationResults from '@/components/ReconciliationResults';
import ProgressIndicator from '@/components/ProgressIndicator';
import ProtectedRoute from '@/components/ProtectedRoute';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type Step = 'upload' | 'processing' | 'results';

export default function Home() {
  return (
    <ProtectedRoute>
      <HomeContent />
    </ProtectedRoute>
  );
}

function HomeContent() {
  const { user, logout } = useAuth();
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

      // Get auth token
      const token = localStorage.getItem('access_token');
      const headers: any = {
        'Content-Type': 'multipart/form-data',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

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
        headers,
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
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <TrendingUp className="w-7 h-7 text-blue-600 mr-2" />
              <h1 className="text-xl font-semibold text-slate-900">Financial Reconciliation</h1>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <User className="w-4 h-4" />
                <span className="font-medium">{user?.email}</span>
              </div>
              <button
                onClick={logout}
                className="flex items-center gap-2 px-4 py-2 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded-lg transition-colors"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Main Content */}
        <AnimatePresence mode="wait">
          {step === 'upload' && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
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
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
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
      <div className="text-center mb-10">
        <h2 className="text-3xl font-semibold text-slate-900 mb-2">Upload Files</h2>
        <p className="text-slate-600">Upload your bank statement and internal ledger to begin reconciliation</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <FileUploadCard
          title="Bank Statement"
          icon={<FileText className="w-8 h-8" />}
          file={bankFile}
          onFileSelect={(file) => onFileSelect('bank', file)}
          acceptedTypes=".csv"
        />
        <FileUploadCard
          title="Internal Ledger"
          icon={<FileText className="w-8 h-8" />}
          file={ledgerFile}
          onFileSelect={(file) => onFileSelect('ledger', file)}
          acceptedTypes=".csv"
        />
      </div>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700"
        >
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        </motion.div>
      )}

      <motion.button
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        onClick={onReconcile}
        disabled={!bankFile || !ledgerFile}
        className="w-full py-3.5 px-6 bg-blue-600 text-white rounded-lg font-medium text-base shadow-sm hover:bg-blue-700 hover:shadow transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
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
      className="card p-6"
    >
      <div className="flex items-center gap-3 mb-4 text-slate-900">
        <div className="text-blue-600">{icon}</div>
        <h3 className="text-lg font-medium">{title}</h3>
      </div>

      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="border-2 border-dashed border-slate-200 rounded-lg p-8 text-center hover:border-blue-400 transition-colors cursor-pointer bg-slate-50"
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
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              className="space-y-2"
            >
              <CheckCircle2 className="w-12 h-12 text-green-600 mx-auto" />
              <p className="text-slate-900 font-medium">{file.name}</p>
              <p className="text-sm text-slate-500">
                {(file.size / 1024).toFixed(2)} KB
              </p>
            </motion.div>
          ) : (
            <div className="space-y-2">
              <Upload className="w-12 h-12 text-slate-400 mx-auto" />
              <p className="text-slate-700">Drop file here or click to upload</p>
              <p className="text-sm text-slate-500">CSV format</p>
            </div>
          )}
        </label>
      </div>

      {file && (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          onClick={() => onFileSelect(null)}
          className="mt-4 text-sm text-red-600 hover:text-red-700"
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
        <Loader2 className="w-16 h-16 text-blue-600 mx-auto animate-spin" />
      </motion.div>

      <h2 className="text-3xl font-semibold text-slate-900 mb-4">
        Processing Reconciliation
      </h2>
      <p className="text-slate-600 mb-8">
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
            className="card p-4"
          >
            <div className="text-blue-600 font-medium mb-2">{step}</div>
            <div className="text-sm text-slate-500">In progress...</div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
