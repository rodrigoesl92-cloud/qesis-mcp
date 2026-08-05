import { NextResponse } from 'next/server';

export const runtime = 'nodejs';

export async function POST(req: Request) {
  try {
    let body;
    try {
      body = await req.json();
    } catch {
      return NextResponse.json({
        jsonrpc: '2.0',
        error: { code: -32700, message: 'Parse error: Invalid JSON' },
        id: null
      }, { status: 400 });
    }

    const { id = null, method, params } = body || {};

    if (method === 'initialize') {
      return NextResponse.json({
        jsonrpc: '2.0',
        result: {
          protocolVersion: '2024-11-05',
          capabilities: {},
          serverInfo: {
            name: 'qesis-mcp-gateway',
            version: '0.0.7'
          }
        },
        id
      });
    }

    return NextResponse.json({
      jsonrpc: '2.0',
      error: { code: -32601, message: `Method not found: ${method}` },
      id
    });
  } catch (error: any) {
    return NextResponse.json({
      jsonrpc: '2.0',
      error: { code: -32603, message: 'Internal error', data: error?.message },
      id: null
    }, { status: 200 });
  }
}

export async function GET() {
  return NextResponse.json({ status: 'QESIS MCP Gateway Online' }, { status: 200 });
}