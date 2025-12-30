'use client';

import { motion } from 'framer-motion';
import { 
  CheckCircle2, 
  AlertTriangle, 
  TrendingUp, 
  Download,
  RefreshCw,
  FileText,
  Ticket,
  BarChart3
} from 'lucide-react';
import { useState } from 'react';
import axios from 'axios';
import DiscrepancyList from './DiscrepancyList';
import SummaryCards from './SummaryCards';
import Charts from './Charts';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ReconciliationResults({
  results,
  reconciliationId,
  onReset,
}: {
  results: any;
  reconciliationId: string;
  onReset: () => void;
}) {
  const [activeTab, setActiveTab] = useState<'summary' | 'discrepancies' | 'tickets'>('summary');

  const handleDownload = async (type: 'csv' | 'summary' | 'readable') => {
    try {
      const response = await axios.get(
        `${API_URL}/api/reports/${reconciliationId}/${type}`,
        { responseType: 'blob' }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `reconciliation_${type}_${reconciliationId}.${type === 'csv' ? 'csv' : type === 'summary' ? 'json' : 'txt'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h2 className="text-4xl font-bold text-white mb-2">
            Reconciliation Complete
          </h2>
          <p className="text-gray-400">
            ID: {reconciliationId.substring(0, 8)}...
          </p>
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={onReset}
          className="px-6 py-3 bg-gray-700/50 hover:bg-gray-700 text-white rounded-lg flex items-center gap-2"
        >
          <RefreshCw className="w-5 h-5" />
          New Reconciliation
        </motion.button>
      </motion.div>

      {/* Summary Cards */}
      <SummaryCards summary={results.summary} />

      {/* Charts */}
      <Charts summary={results.summary} />

      {/* Tabs */}
      <div className="glass-dark rounded-2xl p-6">
        <div className="flex gap-4 mb-6 border-b border-white/10">
          {[
            { id: 'summary', label: 'Summary', icon: BarChart3 },
            { id: 'discrepancies', label: 'Discrepancies', icon: AlertTriangle },
            { id: 'tickets', label: 'Tickets', icon: Ticket },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              <tab.icon className="w-5 h-5" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="mt-6">
          {activeTab === 'summary' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-4"
            >
              <div className="grid md:grid-cols-2 gap-4">
                <div className="glass rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-1">Match Rate</div>
                  <div className="text-3xl font-bold text-white">
                    {((results.summary.matched / (results.summary.matched + results.summary.unmatched_bank + results.summary.unmatched_ledger)) * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="glass rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-1">Processing Time</div>
                  <div className="text-3xl font-bold text-white">
                    {results.summary.processing_time?.toFixed(2) || '0.00'}s
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'discrepancies' && (
            <DiscrepancyList tickets={results.tickets} />
          )}

          {activeTab === 'tickets' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-4"
            >
              <div className="text-white mb-4">
                {results.tickets?.length || 0} tickets generated
              </div>
              {results.tickets?.map((ticket: any, index: number) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="glass rounded-lg p-4 border-l-4 border-purple-500"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-white font-semibold mb-2">
                        {ticket.ticket?.title || ticket.fields?.summary || 'Untitled Ticket'}
                      </h4>
                      <p className="text-gray-400 text-sm">
                        {ticket.ticket?.description || ticket.fields?.description || 'No description'}
                      </p>
                      <div className="flex gap-2 mt-3">
                        <span className="px-2 py-1 bg-purple-500/20 text-purple-300 rounded text-xs">
                          {ticket.ticket?.priority || ticket.fields?.priority?.name || 'Medium'}
                        </span>
                        <span className="px-2 py-1 bg-blue-500/20 text-blue-300 rounded text-xs">
                          {ticket.ticket?.severity || 'Medium'}
                        </span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          )}
        </div>
      </div>

      {/* Download Buttons */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex gap-4"
      >
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => handleDownload('csv')}
          className="flex-1 py-3 px-6 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-semibold flex items-center justify-center gap-2"
        >
          <Download className="w-5 h-5" />
          Download CSV Report
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => handleDownload('summary')}
          className="flex-1 py-3 px-6 bg-gray-700/50 hover:bg-gray-700 text-white rounded-lg font-semibold flex items-center justify-center gap-2"
        >
          <FileText className="w-5 h-5" />
          Download Summary
        </motion.button>
      </motion.div>
    </div>
  );
}

