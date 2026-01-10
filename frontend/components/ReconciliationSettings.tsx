'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Settings, Sliders, ChevronDown, ChevronUp, Info } from 'lucide-react';
import { useState } from 'react';

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
        onChange({
            ...config,
            [key]: value
        });
    };

    return (
        <div className="card border border-slate-200 bg-white">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full px-6 py-4 flex items-center justify-between text-slate-800 hover:bg-slate-50 transition-colors rounded-lg"
            >
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                        <Settings className="w-5 h-5" />
                    </div>
                    <div className="text-left">
                        <div className="font-semibold">Reconciliation Settings</div>
                        <div className="text-sm text-slate-500">Configure matching rules and AI sensitivity</div>
                    </div>
                </div>
                {isOpen ? (
                    <ChevronUp className="w-5 h-5 text-slate-400" />
                ) : (
                    <ChevronDown className="w-5 h-5 text-slate-400" />
                )}
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                    >
                        <div className="p-6 pt-0 space-y-6 border-t border-slate-100 mt-2">
                            <div className="grid md:grid-cols-2 gap-6">
                                {/* Amount Tolerance */}
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between">
                                        <label className="text-sm font-medium text-slate-700 flex items-center gap-2">
                                            Amount Tolerance
                                            <div className="group relative">
                                                <Info className="w-4 h-4 text-slate-400 cursor-help" />
                                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-10">
                                                    Maximum difference allowed in transaction amounts ($)
                                                </div>
                                            </div>
                                        </label>
                                        <span className="text-sm font-semibold text-blue-600">
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
                                        className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                                    />
                                    <div className="flex justify-between text-xs text-slate-500">
                                        <span>Strict ($0.00)</span>
                                        <span>Loose ($100.00)</span>
                                    </div>
                                </div>

                                {/* Date Window */}
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between">
                                        <label className="text-sm font-medium text-slate-700 flex items-center gap-2">
                                            Date Window
                                            <div className="group relative">
                                                <Info className="w-4 h-4 text-slate-400 cursor-help" />
                                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-10">
                                                    Max days difference between transaction dates
                                                </div>
                                            </div>
                                        </label>
                                        <span className="text-sm font-semibold text-blue-600">
                                            +/- {config.dateWindowDays} days
                                        </span>
                                    </div>
                                    <input
                                        type="range"
                                        min="0"
                                        max="30"
                                        step="1"
                                        value={config.dateWindowDays}
                                        onChange={(e) => handleChange('dateWindowDays', parseInt(e.target.value))}
                                        className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                                    />
                                    <div className="flex justify-between text-xs text-slate-500">
                                        <span>Generic (0 days)</span>
                                        <span>Flexible (30 days)</span>
                                    </div>
                                </div>

                                {/* Minimum Confidence */}
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between">
                                        <label className="text-sm font-medium text-slate-700 flex items-center gap-2">
                                            Match Confidence
                                            <div className="group relative">
                                                <Info className="w-4 h-4 text-slate-400 cursor-help" />
                                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-10">
                                                    Minimum AI confidence score to auto-match
                                                </div>
                                            </div>
                                        </label>
                                        <span className="text-sm font-semibold text-blue-600">
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
                                        className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                                    />
                                    <div className="flex justify-between text-xs text-slate-500">
                                        <span>Low (10%)</span>
                                        <span>High (100%)</span>
                                    </div>
                                </div>

                                {/* Ticket Severity */}
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between">
                                        <label className="text-sm font-medium text-slate-700">Ticket Threshold</label>
                                    </div>
                                    <select
                                        value={config.minSeverityForTickets}
                                        onChange={(e) => handleChange('minSeverityForTickets', e.target.value)}
                                        className="w-full p-2.5 border border-slate-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-blue-100 focus:border-blue-500 outline-none transition-all"
                                    >
                                        <option value="low">Create tickets for all issues (Low+)</option>
                                        <option value="medium">Important issues only (Medium+)</option>
                                        <option value="high">Critical issues only (High+)</option>
                                        <option value="critical">Critical emergencies only</option>
                                    </select>
                                </div>
                            </div>

                            {/* Toggles */}
                            <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                                <div className="flex items-center gap-3">
                                    <div className={`w-10 h-6 rounded-full p-1 transition-colors cursor-pointer ${config.enableLlm ? 'bg-blue-600' : 'bg-slate-300'}`}
                                        onClick={() => handleChange('enableLlm', !config.enableLlm)}>
                                        <motion.div
                                            className="w-4 h-4 rounded-full bg-white shadow-sm"
                                            animate={{ x: config.enableLlm ? 16 : 0 }}
                                        />
                                    </div>
                                    <div>
                                        <div className="text-sm font-medium text-slate-700">Enable AI Analysis</div>
                                        <div className="text-xs text-slate-500">Use LLM to explain discrepancies</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
