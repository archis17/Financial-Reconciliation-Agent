'use client';

import { motion } from 'framer-motion';
import { AlertTriangle, Info, CheckCircle2 } from 'lucide-react';

export default function DiscrepancyList({ tickets }: { tickets: any[] }) {
  if (!tickets || tickets.length === 0) {
    return (
      <div className="text-center py-12">
        <CheckCircle2 className="w-16 h-16 text-green-600 mx-auto mb-4" />
        <p className="text-slate-600">No discrepancies found. All transactions matched successfully!</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {tickets.map((ticket: any, index: number) => {
        const ticketData = ticket.ticket || ticket;
        const severity = ticketData.severity || 'medium';
        
        const severityStyles = {
          critical: {
            border: 'border-red-500',
            bg: 'bg-red-50',
            iconBg: 'bg-red-100',
            iconColor: 'text-red-600',
            badge: 'bg-red-100 text-red-700',
          },
          high: {
            border: 'border-orange-500',
            bg: 'bg-orange-50',
            iconBg: 'bg-orange-100',
            iconColor: 'text-orange-600',
            badge: 'bg-orange-100 text-orange-700',
          },
          medium: {
            border: 'border-yellow-500',
            bg: 'bg-yellow-50',
            iconBg: 'bg-yellow-100',
            iconColor: 'text-yellow-600',
            badge: 'bg-yellow-100 text-yellow-700',
          },
          low: {
            border: 'border-blue-500',
            bg: 'bg-blue-50',
            iconBg: 'bg-blue-100',
            iconColor: 'text-blue-600',
            badge: 'bg-blue-100 text-blue-700',
          },
        };

        const style = severityStyles[severity as keyof typeof severityStyles] || severityStyles.medium;

        return (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`card p-6 border-l-4 ${style.border} ${style.bg}`}
          >
            <div className="flex items-start gap-4">
              <div className={`p-2 rounded-lg ${style.iconBg}`}>
                <AlertTriangle className={`w-6 h-6 ${style.iconColor}`} />
              </div>
              
              <div className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-slate-900 font-medium text-lg">
                    {ticketData.title || ticket.fields?.summary || 'Untitled'}
                  </h4>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${style.badge}`}>
                    {severity.toUpperCase()}
                  </span>
                </div>
                
                <p className="text-slate-700 mb-4">
                  {ticketData.description || ticket.fields?.description || ticketData.machine_reason || 'No description available'}
                </p>

                {ticketData.llm_explanation && (
                  <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Info className="w-4 h-4 text-blue-600" />
                      <span className="text-sm font-semibold text-blue-700">AI Explanation</span>
                    </div>
                    <p className="text-gray-700 text-sm">{ticketData.llm_explanation}</p>
                  </div>
                )}

                {ticketData.suggested_action && (
                  <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                    <div className="text-sm font-semibold text-gray-700 mb-1">Suggested Action</div>
                    <p className="text-gray-600 text-sm">{ticketData.suggested_action}</p>
                  </div>
                )}

                {ticketData.amount && (
                  <div className="mt-4 flex gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Amount: </span>
                      <span className="text-gray-900 font-semibold">${ticketData.amount}</span>
                    </div>
                    {ticketData.date && (
                      <div>
                        <span className="text-gray-600">Date: </span>
                        <span className="text-gray-900">{new Date(ticketData.date).toLocaleDateString()}</span>
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
