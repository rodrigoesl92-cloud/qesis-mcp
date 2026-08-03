'use client';

import React, { useState } from 'react';

export default function RetrievalPlayground() {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<any[]>([]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setIsSearching(true);
    
    // Simulating the MCP Gateway JSON-RPC response for the MVP UI
    setTimeout(() => {
      setResults([
        {
          id: 'bundle-entsoe-882',
          source: 'ENTSO-E Grid Telemetry',
          content: 'Metabolic sovereignty choke point detected in cross-border energy flows at node 4.',
          manifestRef: 'sha256:b8a5b5ad5612',
          trustLevel: 'Verified'
        },
        {
          id: 'bundle-emodnet-104',
          source: 'EMODnet Subsea Cables',
          content: 'Data pipeline redundancy is structurally constrained by coastal landing vulnerabilities.',
          manifestRef: 'sha256:c9d1a2b34567',
          trustLevel: 'Verified'
        }
      ]);
      setIsSearching(false);
    }, 800);
  };

  return (
    <div className="p-6 bg-slate-950 text-slate-200 min-h-screen font-sans">
      <div className="max-w-5xl mx-auto space-y-6">
        
        {/* Header & Deterministic Config */}
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 shadow-lg flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">Agentic RAG Workbench</h2>
            <p className="text-slate-400 text-sm">Test deterministic retrieval pipelines against pinned infrastructure indices.</p>
          </div>
          <div className="bg-slate-950 border border-slate-700 p-3 rounded-md text-xs font-mono text-slate-300 space-y-1 text-right">
            <div><span className="text-indigo-400">INDEX_VERSION:</span> v9.0.0</div>
            <div><span className="text-indigo-400">EMBED_MODEL:</span> bge-m3-quantized-onnx</div>
            <div><span className="text-indigo-400">SEED:</span> 42 (CPU-bound)</div>
          </div>
        </div>

        {/* Query Input */}
        <form onSubmit={handleSearch} className="flex gap-4">
          <input 
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., Evaluate metabolic sovereignty constraints in European grid..."
            className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-indigo-500 shadow-inner"
          />
          <button 
            type="submit"
            disabled={isSearching}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-8 rounded-lg shadow-lg transition-colors disabled:opacity-50"
          >
            {isSearching ? 'Retrieving...' : 'Run Query'}
          </button>
        </form>

        {/* Results Pane */}
        {results.length > 0 && (
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 shadow-lg">
            <h3 className="text-lg font-bold text-white mb-4 border-b border-slate-700 pb-2">Retrieved Context Bundles</h3>
            <div className="space-y-4">
              {results.map((result, idx) => (
                <div key={idx} className="bg-slate-950 border border-slate-800 rounded-md p-4 flex flex-col gap-2">
                  <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                    <span className="font-bold text-indigo-400">{result.source}</span>
                    <span className="bg-emerald-900/40 border border-emerald-500/50 text-emerald-400 text-xs px-2 py-1 rounded font-mono">
                      ✓ {result.trustLevel}
                    </span>
                  </div>
                  <p className="text-slate-300 text-sm leading-relaxed">{result.content}</p>
                  <div className="mt-2 pt-2 border-t border-slate-800 text-xs font-mono text-slate-500">
                    Manifest Ref: <span className="text-slate-400">{result.manifestRef}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}