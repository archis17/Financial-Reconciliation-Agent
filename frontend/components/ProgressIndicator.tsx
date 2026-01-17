'use client';

import { motion } from 'framer-motion';

export default function ProgressIndicator({ progress }: { progress: number }) {
  return (
    <div className="w-full space-y-2">
      <div className="flex justify-between items-center text-xs uppercase tracking-wider text-muted-foreground">
        <span>Analysis Progress</span>
        <span>{progress}%</span>
      </div>
      <div className="w-full bg-surface border border-border rounded-full h-2 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="h-full bg-accent rounded-full shadow-[0_0_10px_rgba(204,255,0,0.5)]"
        />
      </div>
    </div>
  );
}
