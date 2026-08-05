export default async function handler(req: any, res: any) {
  res.setHeader('Content-Type', 'application/json');

  if (req.method !== 'POST') {
    return res.status(200).json({ status: 'QESIS MCP Gateway Online' });
  }

  try {
    const body = req.body || {};
    const { id = null, method } = body;

    if (method === 'initialize') {
      return res.status(200).json({
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

    return res.status(200).json({
      jsonrpc: '2.0',
      error: { code: -32601, message: `Method not found: ${method}` },
      id
    });
  } catch (error: any) {
    return res.status(200).json({
      jsonrpc: '2.0',
      error: { code: -32603, message: 'Internal error', data: error?.message },
      id: null
    });
  }
}