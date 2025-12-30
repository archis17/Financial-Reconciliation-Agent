'use client';

import { motion } from 'framer-motion';
import { AlertTriangle, Info, CheckCircle2 } from 'lucide-react';

export default function DiscrepancyList({ tickets }: { tickets: any[] }) {
  if (!tickets || tickets.length === 0) {
    return (
      <div className="text-center py-12">
        <CheckCircle2 className="w-16 h-16 text-green-400 mx-auto mb-4" />
        <p className="text-gray-400">No discrepancies found. All transactions matched successfully!</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {tickets.map((ticket: any, index: number) => {
        const ticketData = ticket.ticket || ticket;
        const severity = ticketData.severity || 'medium';
        
        const severityColors = {
          critical: 'border-red-500 bg-red-500/10',
          high: 'border-orange-500 bg-orange-500/10',
          medium: 'border-yellow-500 bg-yellow-500/10',
          low: 'border-blue-500 bg-blue-500/10',
        };

        return (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`glass rounded-lg p-6 border-l-4 ${severityColors[severity as keyof typeof severityColors] || severityColors.medium}`}
          >
            <div className="flex items-start gap-4">
              <div className={`p-2 rounded-lg ${
                severity === 'critical' ? 'bg-red-500/20' :
                severity === 'high' ? 'bg-orange-500/20' :
                severity === 'medium' ? 'bg-yellow-500/20' :
                'bg-blue-500/20'
              }`}>
                <AlertTriangle className={`w-6 h-6 ${
                  severity === 'critical' ? 'text-red-400' :
                  severity === 'high' ? 'text-orange-400' :
                  severity === 'medium' ? 'text-yellow-400' :
                  'text-blue-400'
                }`} />
              </div>
              
              <div className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-white font-semibold text-lg">
                    {ticketData.title || ticket.fields?.summary || 'Untitled'}
                  </h4>
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    severity === 'critical' ? 'bg-red-500/20 text-red-300' :
                    severity === 'high' ? 'bg-orange-500/20 text-orange-300' :
                    severity === 'medium' ? 'bg-yellow-500/20 text-yellow-300' :
                    'bg-blue-500/20 text-blue-300'
                  }`}>
                    {severity.toUpperCase()}
                  </span>
                </div>
                
                <p className="text-gray-300 mb-4">
                  {ticketData.description || ticket.fields?.description || ticketData.machine_reason || 'No description available'}
                </p>

                {ticketData.llm_explanation && (
                  <div className="mb-4 p-4 bg-purple-500/10 border border-purple-500/20 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Info className="w-4 h-4 text-purple-400" />
                      <span className="text-sm font-semibold text-purple-300">AI Explanation</span>
                    </div>
                    <p className="text-gray-300 text-sm">{ticketData.llm_explanation}</p>
                  </div>
                )}

                {ticketData.suggested_action && (
                  <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                    <div className="text-sm font-semibold text-blue-300 mb-1">Suggested Action</div>
                    <p className="text-gray-300 text-sm">{ticketData.suggested_action}</p>
                  </div>
                )}

                {ticketData.amount && (
                  <div className="mt-4 flex gap-4 text-sm">
                    <div>
                      <span className="text-gray-400">Amount: </span>
                      <span className="text-white font-semibold">${ticketData.amount}</span>
                    </div>
                    {ticketData.date && (
                      <div>
                        <span className="text-gray-400">Date: </span>
                        <span className="text-white">{new Date(ticketData.date).toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}

