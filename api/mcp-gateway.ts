import { NextResponse } from 'next/server';
import crypto from 'crypto';

export async function POST(req: Request) {
  const mcpMethod = req.headers.get('Mcp-Method');
  const auth = req.headers.get('Authorization');

  if (!auth || auth !== `Bearer ${process.env.MCP_SECRET_KEY}`) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const body = await req.json();

    switch (mcpMethod) {
      case 'tools/list':
        return NextResponse.json({
          jsonrpc: '2.0',
          id: body.id,
          result: {
            tools: [{
              name: 'request_fsqca_audit',
              description: 'Enqueues a deterministic fsQCA audit run.',
              inputSchema: {
                type: 'object',
                properties: { dataset_ref: { type: 'string' } },
                required: ['dataset_ref']
              }
            }],
            ttlMs: 3600000 
          }
        }, { headers: { 'Cache-Control': 'public, max-age=3600' } });

      case 'tools/call':
        if (body.params.name === 'request_fsqca_audit') {
          const jobId = crypto.randomUUID();
          
          // QStash / Serverless Queue Bridge Implementation
          const queueRes = await fetch(`https://qstash.upstash.io/v2/publish/${process.env.WORKER_ENDPOINT}`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${process.env.QSTASH_TOKEN}`,
              'Content-Type': 'application/json',
              'Upstash-Message-Id': jobId
            },
            body: JSON.stringify({
              job_id: jobId,
              dataset_ref: body.params.arguments.dataset_ref,
              timestamp: new Date().toISOString()
            })
          });

          if (!queueRes.ok) throw new Error('Queue dispatch failed');

          return NextResponse.json({
            jsonrpc: '2.0',
            id: body.id,
            result: {
              content: [{
                type: 'text',
                text: `Job ${jobId} securely enqueued. Awaiting heavy compute.`
              }],
              meta: { job_id: jobId, status: 'input_required' } 
            }
          });
        }
        break;

      default:
        return NextResponse.json({ error: 'Unsupported MCP Method' }, { status: 400 });
    }
  } catch (error) {
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}