'use client';

import { motion } from 'framer-motion';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export default function Charts({ summary }: { summary: any }) {
  const pieData = [
    { name: 'Matched', value: summary.matched || 0, color: '#10b981' },
    { name: 'Unmatched Bank', value: summary.unmatched_bank || 0, color: '#f59e0b' },
    { name: 'Unmatched Ledger', value: summary.unmatched_ledger || 0, color: '#ef4444' },
  ];

  const barData = [
    { name: 'Matched', value: summary.matched || 0 },
    { name: 'Unmatched', value: (summary.unmatched_bank || 0) + (summary.unmatched_ledger || 0) },
    { name: 'Discrepancies', value: summary.discrepancies || 0 },
  ];

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="card p-6"
      >
        <h3 className="text-xl font-semibold text-gray-900 mb-4">Match Distribution</h3>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
            >
              {pieData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.2 }}
        className="card p-6"
      >
        <h3 className="text-xl font-semibold text-gray-900 mb-4">Reconciliation Overview</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={barData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="name" stroke="#6b7280" />
            <YAxis stroke="#6b7280" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#ffffff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
              }}
            />
            <Bar dataKey="value" fill="#2563eb" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </motion.div>
    </div>
  );
}
