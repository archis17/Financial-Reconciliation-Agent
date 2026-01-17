'use client';

import { motion } from 'framer-motion';
import { CheckCircle2, AlertCircle, FileX, Ticket } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/Card';

export default function SummaryCards({ summary }: { summary: any }) {
  const cards = [
    {
      title: 'Matched',
      value: summary.matched || 0,
      icon: CheckCircle2,
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-400/10',
      borderColor: 'border-emerald-400/20',
    },
    {
      title: 'Unmatched (Bank)',
      value: summary.unmatched_bank || 0,
      icon: FileX,
      color: 'text-amber-400',
      bgColor: 'bg-amber-400/10',
      borderColor: 'border-amber-400/20',
    },
    {
      title: 'Unmatched (Ledger)',
      value: summary.unmatched_ledger || 0,
      icon: FileX,
      color: 'text-orange-400',
      bgColor: 'bg-orange-400/10',
      borderColor: 'border-orange-400/20',
    },
    {
      title: 'Discrepancies',
      value: summary.discrepancies || 0,
      icon: AlertCircle,
      color: 'text-accent',
      bgColor: 'bg-accent/10',
      borderColor: 'border-accent/20',
    },
  ];

  return (
    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card, index) => (
        <motion.div
          key={card.title}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
        >
          <Card className={`border ${card.borderColor} bg-surface/50 backdrop-blur-sm`}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-lg ${card.bgColor}`}>
                  <card.icon className={`w-5 h-5 ${card.color}`} />
                </div>
              </div>
              <div className="text-3xl font-bold font-display tracking-tight text-foreground mb-1">{card.value}</div>
              <div className="text-sm text-muted-foreground font-medium">{card.title}</div>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}
