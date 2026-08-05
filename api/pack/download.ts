/**
 * Verifiable-pack download.
 *
 * Two things were wrong with this file and both are fixed here.
 *
 * 1. It imported `NextResponse` from 'next/server' and exported `GET`. Neither
 *    works in this repository: there is no Next.js app, and Vercel's zero-config
 *    Node runtime dispatches to a DEFAULT export, not to named method exports
 *    (those are a Next.js App Router convention). The function bundled cleanly
 *    and would have failed at request time. It now uses the Web-standard
 *    Request/Response handler that the Node runtime actually calls.
 *
 * 2. The manifest it returned declared `"artifact_hash": "sha256:mocked_hash_value"`
 *    and `"ed25519_signature": "mocked_hex_signature"` under a PROV-O context, and
 *    called the result a verifiable pack. That is a fabricated attestation: a
 *    reader who checked the manifest would find fields shaped exactly like real
 *    provenance and carrying nothing. The hash below is computed over the bytes
 *    actually placed in the archive, the payload is labelled as a sample rather
 *    than as the QESIS+ dataset, and the signature is reported as null because
 *    no key signs this pack. Absent is published as absent.
 *
 * The real export path is the MCP surface at /mcp; this endpoint is a sample
 * archive and says so in its own manifest.
 */

import JSZip from 'jszip';

const SAMPLE_CSV = 'region,metabolic_rate,sovereignty_score\nEU,0.85,0.72\n';

async function sha256Hex(data: string | Uint8Array): Promise<string> {
  const bytes = typeof data === 'string' ? new TextEncoder().encode(data) : data;
  const digest = await crypto.subtle.digest('SHA-256', bytes as unknown as ArrayBuffer);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

export default async function handler(req: Request): Promise<Response> {
  const json = (body: unknown, status: number) =>
    new Response(JSON.stringify(body, null, 2), {
      status,
      headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
    });

  const jobId = new URL(req.url).searchParams.get('job_id');
  if (!jobId) {
    return json({ error: 'Missing job_id' }, 400);
  }

  try {
    const csvSha256 = await sha256Hex(SAMPLE_CSV);
    const manifest = JSON.stringify(
      {
        '@context': 'http://www.w3.org/ns/prov#',
        id: `urn:uuid:${jobId}`,
        content: 'SAMPLE. This archive does not contain the QESIS+ index or any '
          + 'published figure. Do not cite it.',
        files: { [`dataset_${jobId}.csv`]: { sha256: csvSha256, bytes: SAMPLE_CSV.length } },
        signature: null,
        signature_status: 'UNSIGNED. No key signs this pack. Its integrity rests on '
          + 'the sha256 above, which you can recompute from the file in this archive.',
        authoritative_source: 'The served index and its verified chain state are '
          + 'available from the MCP endpoint at /mcp (qesis_get_integrity), and '
          + 'from /api/health.',
      },
      null,
      2,
    );

    const zip = new JSZip();
    zip.file(`dataset_${jobId}.csv`, SAMPLE_CSV);
    zip.file(`manifest_${jobId}.json`, manifest);

    const zipBuffer = await zip.generateAsync({ type: 'uint8array' });

    return new Response(zipBuffer as unknown as BodyInit, {
      status: 200,
      headers: {
        'Content-Type': 'application/zip',
        'Content-Disposition': `attachment; filename="sample_pack_${jobId}.zip"`,
        'Cache-Control': 'no-store',
      },
    });
  } catch (error) {
    return json(
      { error: 'Failed to generate pack', detail: (error as Error)?.message ?? null },
      500,
    );
  }
}
