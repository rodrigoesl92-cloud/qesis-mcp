# SCOUT intake: UN Comtrade as the SDI axis source

**2026-08-15 · KG-4 · Retrieved via Exa · Routes to SENTINEL `validate_intake`,
then COUNSEL for the licence limb as second opinion. Not admitted by this note.**

Provenance discipline applies: origin, publisher, licence, retrieval date. All
fetched content is untrusted input and nothing in the source pages is treated as
an instruction.

| Field | Value |
|---|---|
| Publisher | United Nations Statistics Division (UNSD) |
| Product | UN Comtrade, comtradeapi.un.org |
| Origin | uncomtrade.org documentation, comtradeplus.un.org |
| Retrieved | 2026-08-15 |
| Licence | Licence agreement at comtrade.un.org/licenseagreement.html. Internal use free; re-dissemination restricted |
| Coverage | Approximately 200 reporters, over 99 percent of world merchandise trade |

---

## 1. Coverage clears the BIG gate comfortably

Roughly 200 reporters against a 35-state sample. The 27-of-35 minimum that
`v9_sfc_scaffold.json` derives from the 0.75 ratio is not the binding
constraint here, and it was for SFC. That is the reason SDI displaced SFC under
D-111 and this confirms the premise rather than re-litigating it.

Bilateral asymmetry is documented by the publisher, which matters: importer and
exporter report the same flow differently, so a dependency measure must declare
which side it reads and stay on that side.

## 2. The licence is workable, and it is conditional. COUNSEL owns this limb.

Read carefully, because the headline sentence and the operative rule point in
different directions.

- Headline: "UN Comtrade data are provided for internal use only and may not be
  re-disseminated in any form without UNSD's permission."
- Operative: "If data being re-disseminated are substantially different from the
  data provided in UN Comtrade, then a license to distribute with a fee shall
  not apply." And: "Transformed data from UN Comtrade is no longer subject to
  copyright restrictions."

A composite axis derived from trade flows is transformed, not re-disseminated,
so no distribution licence fee applies. **But** the FAQ attaches a standing
condition: "you must maintain an active premium subscription", justified as
keeping the transformation refreshed against revisions.

Consequences for the business model, which is the CC-BY-NC demo against
institutional licence split:

1. Publishing an SDI axis derived from Comtrade appears to sit inside the
   transformed-data exemption. That is a reading of the terms, not advice.
2. Bulk file access is premium only. The free tier is a preview API with limited
   endpoints. An automated pipeline needs a paid key.
3. Premium individual allows 5000 API calls per day. Institutional is unlimited.
4. Publishing raw or near-raw Comtrade rows on the served surface would leave
   the exemption and enter re-dissemination. The axis must be a derivation, and
   the served payload must not carry recoverable source rows.

**COUNSEL disposition: YELLOW.** Workable, and it introduces a recurring cost
and an ongoing obligation where the ecosystem currently has neither. It needs a
row in the obligations register before any pipeline is built, and Article 14
Decision 3, thresholds for automated API token use and cloud provisioning, is
unsigned and is the gate this crosses.

## 3. The finding that actually matters, and it is architectural

> **Single-version policy.** "UN Comtrade maintains only one version of each
> dataset. Once data are updated, only the most recent version is accessible.
> There is no archive of earlier versions." Data are revised continuously as
> countries submit corrections.

This collides directly with how this ecosystem establishes provenance. Every
vintage pins its inputs by SHA-256: `v8_qesis_country_scores.csv` at
`022e4f0b…`, `cloud_regions_master.csv` at `44d203ae…`. A reader is invited to
re-derive the number from the source.

For a Comtrade-derived axis that invitation cannot be honoured. Re-fetching the
same query next quarter can return different bytes, with no way to request the
bytes that produced the vintage and no error to signal the difference. The hash
would then attest a local copy rather than a retrievable source, which is a
weaker claim than every other axis makes and must not be presented as the same
claim.

This is not a reason to refuse the source. It is a reason to admit it with a
declared provenance class. Three options, for ANALYST and SENTINEL to rule on:

| Option | What it does | Cost |
|---|---|---|
| **Snapshot custody** | Keep the retrieved bulk file as a first-class committed artefact and hash that. Lineage cites the snapshot, not the endpoint | Storage, and the snapshot becomes the source of record |
| **Declared irreproducibility** | Publish the axis with a provenance class stating the source carries no version archive, alongside retrieval date and query | Honest, cheap, and weaker than every other axis |
| **Refuse** | Find a trade source with versioned releases | Probably none exists at this coverage |

Snapshot custody is the only option that preserves the property the index
already claims everywhere else. It is also the option that converts a licence
question into a storage question, and COUNSEL notes that retaining a bulk file
is closer to the re-dissemination boundary than deriving from it in flight.
Those two pull in opposite directions and the tension is the decision.

## 4. What SCOUT did not verify

- Whether the licence agreement text at comtrade.un.org/licenseagreement.html
  says the same thing as the help-centre summaries. It was not fetched. The
  agreement governs, the help centre does not, and no admission should rest on a
  summary of terms.
- Current subscription pricing. Not published on the pages retrieved.
- Whether any of the 35 sample states are non-reporters or chronic late
  reporters, which would reintroduce a coverage question the headline number
  hides.

## 5. Recommended next step, and it is not ingestion

Do not build a pipeline. Draft the SDI ingestion contract first, in the shape of
`prove_axis_sfc_contract.py`, and make it refuse by name: revenue proxies,
re-exports counted as domestic production, mirror statistics silently
substituted for a non-reporter, aggregate rows, and any row whose provenance
class is not declared. SFC's contract caught a 26-against-27 threshold error
before a single record was ingested. That is the sequence that worked.
