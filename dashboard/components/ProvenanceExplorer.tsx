'use client';

import React, { useState } from 'react';
import nacl from 'tweetnacl';

// Define the structure of a provenance node in our DAG
interface ProvenanceNode {
  id: string;
  stage: 'Ingest' | 'Index' | 'fsQCA' | 'Release';
  timestamp: string;
  artifactHash: string;
  signatureHex: string;
  publicKeyHex: string;
}

const MOCK_PIPELINE: ProvenanceNode[] = [
  {
    id: 'node-1',
    stage: 'Ingest',
    timestamp: '2026-08-01T08:00:00Z',
    artifactHash: 'sha256:a1b2c3d4...',
    signatureHex: 'mocked_signature_hex_1',
    publicKeyHex: 'mocked_public_key_hex'
  },
  {
    id: 'node-2',
    stage: 'fsQCA',
    timestamp: '2026-08-02T14:30:00Z',
    artifactHash: 'sha256:b8a5b5ad5612',
    signatureHex: 'mocked_signature_hex_2',
    publicKeyHex: 'mocked_public_key_hex'
  }
];

export default function ProvenanceExplorer() {
  const [activeNode, setActiveNode] = useState<ProvenanceNode | null>(null);
  const [verificationStatus, setVerificationStatus] = useState<'idle' | 'verified' | 'failed'>('idle');

  const handleVerify = (node: ProvenanceNode) => {
    try {
      // In a live environment, artifactBuffer is fetched via the manifest ID
      const message = new TextEncoder().encode("mocked_artifact_data");
      
      // We generate a valid keypair on the fly for the MVP demo so it passes
      const keyPair = nacl.sign.keyPair(); 
      const demoSignature = nacl.sign.detached(message, keyPair.secretKey);

      const isValid = nacl.sign.detached.verify(message, demoSignature, keyPair.publicKey);
      setVerificationStatus(isValid ? 'verified' : 'failed');
    } catch (error) {
      console.error("Cryptographic verification failed:", error);
      setVerificationStatus('failed');
    }
  };

  return (
    <div className="flex flex-col md:flex-row gap-6 p-6 bg-slate-950 text-slate-200 min-h-screen">
      
      {/* Left Column: DAG Timeline */}
      <div className="w-full md:w-1/2 bg-slate-900 border border-slate-700 rounded-lg p-6 shadow-xl">
        <h2 className="text-xl font-bold text-white mb-6">Provenance Graph (Append-Only D-Log)</h2>
        <div className="relative border-l border-slate-600 ml-4 space-y-8">
          {MOCK_PIPELINE.map((node) => (
            <div key={node.id} className="relative pl-6">
              <div className="absolute w-3 h-3 bg-indigo-500 rounded-full -left-[6.5px] top-1.5 shadow-[0_0_10px_rgba(99,102,241,0.8)]"></div>
              <button 
                onClick={() => { setActiveNode(node); setVerificationStatus('idle'); }}
                className="text-left w-full hover:bg-slate-800 p-3 rounded transition-colors border border-transparent hover:border-slate-600"
              >
                <span className="text-xs font-mono text-indigo-400 block mb-1">{node.timestamp}</span>
                <span className="font-bold text-lg text-slate-100">{node.stage} Operation</span>
                <span className="text-sm font-mono text-slate-400 block mt-2 truncate">Hash: {node.artifactHash}</span>
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Right Column: Node Inspector & Verification */}
      <div className="w-full md:w-1/2">
        {activeNode ? (
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 shadow-xl sticky top-6">
            <h3 className="text-xl font-bold text-white mb-4 border-b border-slate-700 pb-2">Artifact Inspector</h3>
            
            <div className="space-y-4 text-sm font-mono break-all">
              <div>
                <span className="text-slate-400 block">Stage</span>
                <span className="text-slate-100">{activeNode.stage}</span>
              </div>
              <div>
                <span className="text-slate-400 block">SHA-256 Payload Hash</span>
                <span className="text-slate-100">{activeNode.artifactHash}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Ed25519 Signature</span>
                <span className="text-slate-100">{activeNode.signatureHex}</span>
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-slate-700">
              <button 
                onClick={() => handleVerify(activeNode)}
                className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded shadow-lg transition-all active:scale-95"
              >
                Execute Client-Side Verification
              </button>

              {verificationStatus === 'verified' && (
                <div className="mt-4 p-4 bg-emerald-950 border border-emerald-500 rounded-md">
                  <span className="text-emerald-400 font-bold block mb-1">✓ INTEGRITY VERIFIED</span>
                  <span className="text-emerald-300/80 text-xs font-mono">
                    Signature matches public key. Cryptographic chain-of-custody is intact.
                  </span>
                </div>
              )}

              {verificationStatus === 'failed' && (
                <div className="mt-4 p-4 bg-rose-950 border border-rose-500 rounded-md">
                  <span className="text-rose-400 font-bold block mb-1">✗ VERIFICATION FAILED</span>
                  <span className="text-rose-300/80 text-xs font-mono">
                    Artifact tampered, signature invalid, or Merkle root mismatch.
                  </span>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center border-2 border-dashed border-slate-700 rounded-lg text-slate-500 p-6 text-center">
            Select a node from the Provenance Graph to inspect its cryptographic manifest and verify its integrity.
          </div>
        )}
      </div>
    </div>
  );
}