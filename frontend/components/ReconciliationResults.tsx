'use client';

import { motion } from 'framer-motion';
import { 
  AlertTriangle, 
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
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { cn } from '@/lib/utils';

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
      const token = localStorage.getItem('access_token');
      const headers: any = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const response = await axios.get(
        `${API_URL}/api/reports/${reconciliationId}/${type}`,
        { 
          responseType: 'blob',
          headers
        }
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
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h2 className="text-3xl font-display font-bold text-foreground mb-1">
            Analysis Complete
          </h2>
          <p className="text-muted-foreground font-mono text-sm">
            ID: {reconciliationId.substring(0, 8)}...
          </p>
        </div>
        <Button
          onClick={onReset}
          variant="ghost"
          className="text-muted-foreground hover:text-foreground hover:bg-surface border border-transparent hover:border-border"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Reset Protocol
        </Button>
      </motion.div>

      <SummaryCards summary={results.summary} />

      <Charts summary={results.summary} />

      {/* Tabs */}
      <Card>
        <div className="flex border-b border-border">
          {[
            { id: 'summary', label: 'Summary', icon: BarChart3 },
            { id: 'discrepancies', label: 'Discrepancies', icon: AlertTriangle },
            { id: 'tickets', label: 'Tickets', icon: Ticket },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={cn(
                "flex items-center gap-2 px-6 py-4 transition-all font-medium text-sm relative",
                activeTab === tab.id
                  ? "text-primary bg-primary/5"
                  : "text-muted-foreground hover:text-foreground hover:bg-surface/50"
              )}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
              {activeTab === tab.id && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary"
                />
              )}
            </button>
          ))}
        </div>

        <CardContent className="p-6">
          {activeTab === 'summary' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-4"
            >
              <div className="grid md:grid-cols-2 gap-4">
                <div className="p-4 bg-surface border border-border rounded-lg">
                  <div className="text-sm text-muted-foreground mb-1">Match Rate</div>
                  <div className="text-3xl font-bold text-foreground font-display">
                    {((results.summary.matched / (results.summary.matched + results.summary.unmatched_bank + results.summary.unmatched_ledger)) * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="p-4 bg-surface border border-border rounded-lg">
                  <div className="text-sm text-muted-foreground mb-1">Processing Time</div>
                  <div className="text-3xl font-bold text-foreground font-display">
                    {results.summary.processing_time?.toFixed(2) || '0.00'}<span className="text-lg text-muted-foreground font-sans font-normal ml-1">s</span>
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
              <div className="text-muted-foreground mb-4 text-sm font-medium">
                {results.tickets?.length || 0} tickets generated in system
              </div>
              {results.tickets?.map((ticket: any, index: number) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="p-4 bg-surface border-l-4 border-l-primary border border-border rounded-r-lg"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-foreground font-semibold mb-2">
                        {ticket.ticket?.title || ticket.fields?.summary || 'Untitled'}
                      </h4>
                      <p className="text-muted-foreground text-sm">
                        {ticket.ticket?.description || ticket.fields?.description || 'No description'}
                      </p>
                      <div className="flex gap-2 mt-3">
                        <span className="px-2 py-0.5 border border-primary/20 bg-primary/5 text-primary rounded text-xs">
                          {ticket.ticket?.priority || ticket.fields?.priority?.name || 'Medium'}
                        </span>
                        <span className="px-2 py-0.5 border border-border bg-surface text-muted-foreground rounded text-xs">
                          {ticket.ticket?.severity || 'Medium'}
                        </span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          )}
        </CardContent>
      </Card>

      {/* Download Buttons */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex gap-4"
      >
        <Button
          onClick={() => handleDownload('csv')}
          className="flex-1"
          variant="primary"
          size="lg"
        >
          <Download className="w-4 h-4 mr-2" />
          Export CSV Report
        </Button>
        <Button
          onClick={() => handleDownload('summary')}
          className="flex-1"
          variant="secondary"
          size="lg"
        >
          <FileText className="w-4 h-4 mr-2" />
          Export Summary
        </Button>
      </motion.div>
    </div>
  );
}
