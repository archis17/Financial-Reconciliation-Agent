'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Settings, ChevronDown, ChevronUp, Info } from 'lucide-react';
import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { cn } from '@/lib/utils';

export interface ReconciliationConfig {
    amountTolerance: number;
    dateWindowDays: number;
    minConfidence: number;
    enableLlm: boolean;
    minSeverityForTickets: 'low' | 'medium' | 'high' | 'critical';
}

interface Props {
    config: ReconciliationConfig;
    onChange: (config: ReconciliationConfig) => void;
}

export default function ReconciliationSettings({ config, onChange }: Props) {
    const [isOpen, setIsOpen] = useState(false);

    const handleChange = (key: keyof ReconciliationConfig, value: any) => {
        onChange({ ...config, [key]: value });
    };

    return (
        <Card className="overflow-hidden bg-background/50 border-border">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full px-6 py-4 flex items-center justify-between text-foreground hover:bg-surface/50 transition-colors"
            >
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-surface rounded-lg text-primary border border-border">
                        <Settings className="w-4 h-4" />
                    </div>
                    <div className="text-left">
                        <div className="font-semibold text-sm">Calibration</div>
                        <div className="text-xs text-muted-foreground">Configure matching parameters</div>
                    </div>
                </div>
                {isOpen ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                    >
                        <div className="p-6 pt-0 space-y-8 border-t border-border mt-2">
                            <div className="grid md:grid-cols-2 gap-8 pt-4">
                                {/* Amount Tolerance */}
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <label className="text-sm font-medium text-foreground flex items-center gap-2">
                                            Amount Tolerance
                                        </label>
                                        <span className="text-sm font-mono text-primary bg-primary/10 px-2 py-0.5 rounded">
                                            ${config.amountTolerance.toFixed(2)}
                                        </span>
                                    </div>
                                    <input
                                        type="range"
                                        min="0"
                                        max="100"
                                        step="0.01"
                                        value={config.amountTolerance}
                                        onChange={(e) => handleChange('amountTolerance', parseFloat(e.target.value))}
                                        className="w-full h-1 bg-surface rounded-lg appearance-none cursor-pointer accent-accent"
                                    />
                                </div>

                                {/* Date Window */}
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <label className="text-sm font-medium text-foreground flex items-center gap-2">
                                            Date Window
                                        </label>
                                        <span className="text-sm font-mono text-primary bg-primary/10 px-2 py-0.5 rounded">
                                            +/- {config.dateWindowDays}d
                                        </span>
                                    </div>
                                    <input
                                        type="range"
                                        min="0"
                                        max="30"
                                        step="1"
                                        value={config.dateWindowDays}
                                        onChange={(e) => handleChange('dateWindowDays', parseInt(e.target.value))}
                                        className="w-full h-1 bg-surface rounded-lg appearance-none cursor-pointer accent-accent"
                                    />
                                </div>

                                {/* Minimum Confidence */}
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <label className="text-sm font-medium text-foreground flex items-center gap-2">
                                            Match Confidence
                                        </label>
                                        <span className="text-sm font-mono text-primary bg-primary/10 px-2 py-0.5 rounded">
                                            {Math.round(config.minConfidence * 100)}%
                                        </span>
                                    </div>
                                    <input
                                        type="range"
                                        min="0.1"
                                        max="1.0"
                                        step="0.05"
                                        value={config.minConfidence}
                                        onChange={(e) => handleChange('minConfidence', parseFloat(e.target.value))}
                                        className="w-full h-1 bg-surface rounded-lg appearance-none cursor-pointer accent-accent"
                                    />
                                </div>

                                {/* Ticket Severity */}
                                <div className="space-y-4">
                                    <label className="text-sm font-medium text-foreground">Ticket Threshold</label>
                                    <select
                                        value={config.minSeverityForTickets}
                                        onChange={(e) => handleChange('minSeverityForTickets', e.target.value)}
                                        className="w-full p-2.5 bg-surface border border-border rounded-md text-sm text-foreground focus:ring-1 focus:ring-primary outline-none"
                                    >
                                        <option value="low">All Issues (Low+)</option>
                                        <option value="medium">Important (Medium+)</option>
                                        <option value="high">Critical (High+)</option>
                                        <option value="critical">Emergency Only</option>
                                    </select>
                                </div>
                            </div>

                            {/* Toggles */}
                            <div className="flex items-center justify-between pt-4 border-t border-border">
                                <div className="flex items-center gap-4">
                                    <div 
                                        className={cn(
                                            "w-10 h-6 rounded-full p-1 transition-colors cursor-pointer",
                                            config.enableLlm ? "bg-primary" : "bg-surface border border-border"
                                        )}
                                        onClick={() => handleChange('enableLlm', !config.enableLlm)}
                                    >
                                        <motion.div
                                            className="w-4 h-4 rounded-full bg-white shadow-sm"
                                            animate={{ x: config.enableLlm ? 16 : 0 }}
                                        />
                                    </div>
                                    <div>
                                        <div className="text-sm font-medium text-foreground">AI Neural Analysis</div>
                                        <div className="text-xs text-muted-foreground">Use LLM for discrepancy explanation</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </Card>
    );
}
