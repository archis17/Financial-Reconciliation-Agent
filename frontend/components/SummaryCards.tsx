'use client';

import { motion } from 'framer-motion';
import { CheckCircle2, AlertCircle, TrendingUp, FileX } from 'lucide-react';

export default function SummaryCards({ summary }: { summary: any }) {
  const cards = [
    {
      title: 'Matched',
      value: summary.matched || 0,
      icon: CheckCircle2,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
    },
    {
      title: 'Unmatched (Bank)',
      value: summary.unmatched_bank || 0,
      icon: FileX,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
    },
    {
      title: 'Unmatched (Ledger)',
      value: summary.unmatched_ledger || 0,
      icon: FileX,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      borderColor: 'border-orange-200',
    },
    {
      title: 'Discrepancies',
      value: summary.discrepancies || 0,
      icon: AlertCircle,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
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
          whileHover={{ scale: 1.02, y: -2 }}
          className={`card p-6 border-2 ${card.borderColor} hover:shadow-lg transition-all`}
        >
          <div className="flex items-center justify-between mb-4">
            <div className={`p-3 rounded-lg ${card.bgColor}`}>
              <card.icon className={`w-6 h-6 ${card.color}`} />
            </div>
          </div>
          <div className="text-3xl font-bold text-gray-900 mb-1">{card.value}</div>
          <div className="text-sm text-gray-600">{card.title}</div>
        </motion.div>
      ))}
    </div>
  );
}
