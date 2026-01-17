'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload,
  FileText,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  ArrowRight,
  Loader2,
  LogOut,
  User,
  LayoutDashboard
} from 'lucide-react';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';
import ReconciliationResults from '@/components/ReconciliationResults';
import ProgressIndicator from '@/components/ProgressIndicator';
import ProtectedRoute from '@/components/ProtectedRoute';
import ReconciliationSettings, { ReconciliationConfig } from '@/components/ReconciliationSettings';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { cn } from '@/lib/utils';

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
    if (type === 'bank') setBankFile(file);
    else setLedgerFile(file);
  };

  const handleReconcile = async (config?: ReconciliationConfig) => {
    if (!bankFile || !ledgerFile) {
      setError('Please upload both bank statement and ledger files');
      return;
    }

    const matchConfig = config || {
      amountTolerance: 5.0,
      dateWindowDays: 7,
      minConfidence: 0.6,
      enableLlm: true,
      minSeverityForTickets: 'low'
    };

    setProcessing(true);
    setError(null);
    setStep('processing');
    setProgress(0);

    try {
      const formData = new FormData();
      formData.append('bank_file', bankFile);
      formData.append('ledger_file', ledgerFile);
      formData.append('amount_tolerance', matchConfig.amountTolerance.toString());
      formData.append('date_window_days', matchConfig.dateWindowDays.toString());
      formData.append('min_confidence', matchConfig.minConfidence.toString());
      formData.append('enable_llm', matchConfig.enableLlm.toString());
      formData.append('min_severity_for_tickets', matchConfig.minSeverityForTickets);

      const token = localStorage.getItem('access_token');
      const headers: any = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

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
        timeout: 300000,
      });

      clearInterval(progressInterval);
      setProgress(100);

      setTimeout(() => {
        setResults(response.data);
        setStep('results');
        setProcessing(false);
      }, 500);

    } catch (err: any) {
      console.error('Reconcile error', err.response ?? err);
      const serverData = err.response?.data;
      const serverMessage = serverData?.message || serverData?.detail;
      setError(serverMessage || (serverData ? JSON.stringify(serverData) : err.message) || 'An error occurred during reconciliation');
      setProcessing(false);
      setStep('upload');
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground font-sans selection:bg-primary/20">
      {/* Header */}
      <header className="border-b border-border bg-surface/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <div className="bg-primary/10 p-2 rounded-lg">
                <LayoutDashboard className="w-5 h-5 text-primary" />
              </div>
              <h1 className="text-xl font-bold font-display tracking-tight">FinRec<span className="text-primary">.AI</span></h1>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-sm text-muted-foreground px-3 py-1.5 rounded-full bg-surface border border-border">
                <User className="w-4 h-4" />
                <span className="font-medium">{user?.email}</span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={logout}
                className="text-muted-foreground hover:text-foreground"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
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
      </main>
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
  onReconcile: (config: ReconciliationConfig) => void;
  error: string | null;
}) {
  const [config, setConfig] = useState<ReconciliationConfig>({
    amountTolerance: 5.0,
    dateWindowDays: 7,
    minConfidence: 0.6,
    enableLlm: true,
    minSeverityForTickets: 'low'
  });
  
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-display font-bold">Initiate Protocol</h2>
        <p className="text-muted-foreground">Upload financial datasets to begin atomic reconciliation</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <FileUploadCard
          title="Bank Statement"
          icon={<TrendingUp className="w-6 h-6" />}
          file={bankFile}
          onFileSelect={(file) => onFileSelect('bank', file)}
          acceptedTypes=".csv"
        />
        <FileUploadCard
          title="Internal Ledger"
          icon={<FileText className="w-6 h-6" />}
          file={ledgerFile}
          onFileSelect={(file) => onFileSelect('ledger', file)}
          acceptedTypes=".csv"
        />
      </div>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-red-900/20 border border-red-900/50 rounded-lg text-red-200 flex items-center gap-3"
        >
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </motion.div>
      )}

      <ReconciliationSettings config={config} onChange={setConfig} />

      <div className="flex justify-center pt-4">
        <Button
          size="lg"
          onClick={() => onReconcile(config)}
          disabled={!bankFile || !ledgerFile}
          className="w-full md:w-auto min-w-[200px]"
          variant="primary"
        >
          <span>Start Analysis</span>
          <ArrowRight className="ml-2 w-4 h-4" />
        </Button>
      </div>
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
    if (files.length > 0) onFileSelect(files[0]);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) onFileSelect(e.target.files[0]);
  };

  return (
    <Card className={cn(
      "border-dashed transition-colors",
      file ? "border-primary/50 bg-primary/5" : "hover:border-primary/50"
    )}>
      <CardContent className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-surface rounded-md text-primary ring-1 ring-white/10">{icon}</div>
          <h3 className="font-semibold">{title}</h3>
        </div>

        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          className="rounded-lg p-8 text-center transition-all cursor-pointer border border-transparent hover:bg-surface/50"
        >
          <input
            type="file"
            accept={acceptedTypes}
            onChange={handleFileInput}
            className="hidden"
            id={`file-input-${title}`}
          />
          <label htmlFor={`file-input-${title}`} className="cursor-pointer block">
            {file ? (
              <motion.div
                initial={{ scale: 0.9 }}
                animate={{ scale: 1 }}
                className="space-y-2"
              >
                <CheckCircle2 className="w-10 h-10 text-accent mx-auto" />
                <p className="font-medium text-foreground">{file.name}</p>
                <p className="text-xs text-muted-foreground uppercase tracking-wider">
                  {(file.size / 1024).toFixed(2)} KB
                </p>
              </motion.div>
            ) : (
              <div className="space-y-3">
                <div className="w-12 h-12 bg-surface rounded-full flex items-center justify-center mx-auto ring-1 ring-white/5">
                  <Upload className="w-5 h-5 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground group-hover:text-foreground">Click to upload</p>
                  <p className="text-xs text-muted-foreground/50 mt-1">or drag and drop CSV</p>
                </div>
              </div>
            )}
          </label>
        </div>

        {file && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onFileSelect(null)}
            className="w-full mt-4 text-red-400 hover:text-red-300 hover:bg-red-900/20"
          >
            Remove File
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

function ProcessingStep({ progress }: { progress: number }) {
  return (
    <div className="max-w-xl mx-auto text-center space-y-8 py-12">
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: "spring", stiffness: 200 }}
        className="relative mx-auto w-24 h-24 flex items-center justify-center"
      >
        <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full" />
        <Loader2 className="w-12 h-12 text-primary animate-spin relative z-10" />
      </motion.div>

      <div className="space-y-2">
        <h2 className="text-2xl font-display font-bold">Processing Data</h2>
        <p className="text-muted-foreground">Neural matching engine active...</p>
      </div>

      <ProgressIndicator progress={progress} />

      <div className="grid grid-cols-3 gap-3">
        {['Ingesting', 'Matching', 'Analyzing'].map((step, i) => (
          <motion.div
            key={step}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.2 }}
            className="p-3 bg-surface border border-border rounded-lg text-xs font-medium text-muted-foreground"
          >
            {step}
          </motion.div>
        ))}
      </div>
    </div>
  );
}
