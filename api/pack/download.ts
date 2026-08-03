import { NextResponse } from 'next/server';
import JSZip from 'jszip';

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const jobId = searchParams.get('job_id');

  if (!jobId) {
    return NextResponse.json({ error: 'Missing job_id' }, { status: 400 });
  }

  try {
    const mockCsvContent = "region,metabolic_rate,sovereignty_score\nEU,0.85,0.72";
    const mockManifest = JSON.stringify({
      "@context": "http://www.w3.org/ns/prov#",
      "id": `urn:uuid:${jobId}`,
      "artifact_hash": "sha256:mocked_hash_value",
      "ed25519_signature": "mocked_hex_signature"
    }, null, 2);

    const zip = new JSZip();
    zip.file(`dataset_${jobId}.csv`, mockCsvContent);
    zip.file(`manifest_${jobId}.json`, mockManifest);
    zip.file(`merkle_proof.txt`, "Anchored to Git Release: fc5424e");

    const zipBuffer = await zip.generateAsync({ type: 'nodebuffer' });

    return new NextResponse(zipBuffer, {
      status: 200,
      headers: {
        'Content-Type': 'application/zip',
        'Content-Disposition': `attachment; filename="verifiable_pack_${jobId}.zip"`,
      },
    });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to generate pack' }, { status: 500 });
  }
}