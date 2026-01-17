'use client';

import { motion } from 'framer-motion';
import { AlertTriangle, Info, CheckCircle2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/Card';

export default function DiscrepancyList({ tickets }: { tickets: any[] }) {
  if (!tickets || tickets.length === 0) {
    return (
      <div className="text-center py-12">
        <CheckCircle2 className="w-16 h-16 text-emerald-500 mx-auto mb-4" />
        <p className="text-muted-foreground">No discrepancies found. All transactions matched successfully.</p>
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
            border: 'border-red-500/50',
            bg: 'bg-red-500/5',
            icon: 'text-red-500',
            badge: 'bg-red-500/10 text-red-500 border-red-500/20',
          },
          high: {
            border: 'border-orange-500/50',
            bg: 'bg-orange-500/5',
            icon: 'text-orange-500',
            badge: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
          },
          medium: {
            border: 'border-yellow-500/50',
            bg: 'bg-yellow-500/5',
            icon: 'text-yellow-500',
            badge: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
          },
          low: {
            border: 'border-blue-500/50',
            bg: 'bg-blue-500/5',
            icon: 'text-blue-500',
            badge: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
          },
        };

        const style = severityStyles[severity as keyof typeof severityStyles] || severityStyles.medium;

        return (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Card className={`border-l-4 ${style.border} ${style.bg}`}>
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className={`p-2 rounded-lg bg-surface border border-border`}>
                    <AlertTriangle className={`w-5 h-5 ${style.icon}`} />
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-lg text-foreground">
                        {ticketData.title || ticket.fields?.summary || 'Untitled'}
                      </h4>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium border ${style.badge} uppercase tracking-wide`}>
                        {severity}
                      </span>
                    </div>
                    
                    <p className="text-muted-foreground mb-4 text-sm">
                      {ticketData.description || ticket.fields?.description || ticketData.machine_reason || 'No description available'}
                    </p>

                    {ticketData.llm_explanation && (
                      <div className="mb-4 p-4 bg-primary/5 border border-primary/20 rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <Info className="w-4 h-4 text-primary" />
                          <span className="text-sm font-semibold text-primary">AI Inference</span>
                        </div>
                        <p className="text-foreground/80 text-sm leading-relaxed">{ticketData.llm_explanation}</p>
                      </div>
                    )}

                    {ticketData.suggested_action && (
                      <div className="p-4 bg-surface border border-border rounded-lg">
                        <div className="text-sm font-semibold text-foreground mb-1">Recommended Action</div>
                        <p className="text-muted-foreground text-sm">{ticketData.suggested_action}</p>
                      </div>
                    )}

                    {ticketData.amount && (
                      <div className="mt-4 flex gap-6 text-sm border-t border-border pt-3">
                        <div>
                          <span className="text-muted-foreground">Amount: </span>
                          <span className="text-foreground font-mono font-medium">${ticketData.amount}</span>
                        </div>
                        {ticketData.date && (
                          <div>
                            <span className="text-muted-foreground">Date: </span>
                            <span className="text-foreground font-mono font-medium">{new Date(ticketData.date).toLocaleDateString()}</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        );
      })}
    </div>
  );
}
