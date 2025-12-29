'use client';

import { motion } from 'framer-motion';
import { CheckCircle2, AlertCircle, TrendingUp, FileX } from 'lucide-react';

export default function SummaryCards({ summary }: { summary: any }) {
  const cards = [
    {
      title: 'Matched',
      value: summary.matched || 0,
      icon: CheckCircle2,
      color: 'green',
      gradient: 'from-green-500 to-emerald-500',
    },
    {
      title: 'Unmatched (Bank)',
      value: summary.unmatched_bank || 0,
      icon: FileX,
      color: 'yellow',
      gradient: 'from-yellow-500 to-orange-500',
    },
    {
      title: 'Unmatched (Ledger)',
      value: summary.unmatched_ledger || 0,
      icon: FileX,
      color: 'orange',
      gradient: 'from-orange-500 to-red-500',
    },
    {
      title: 'Discrepancies',
      value: summary.discrepancies || 0,
      icon: AlertCircle,
      color: 'red',
      gradient: 'from-red-500 to-pink-500',
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
          whileHover={{ scale: 1.05, y: -5 }}
          className="glass-dark rounded-2xl p-6 border border-white/10 hover:border-purple-500/50 transition-all"
        >
          <div className="flex items-center justify-between mb-4">
            <div className={`p-3 rounded-lg bg-gradient-to-br ${card.gradient} bg-opacity-20`}>
              <card.icon className={`w-6 h-6 text-${card.color}-400`} />
            </div>
          </div>
          <div className="text-3xl font-bold text-white mb-1">{card.value}</div>
          <div className="text-sm text-gray-400">{card.title}</div>
        </motion.div>
      ))}
    </div>
  );
}

