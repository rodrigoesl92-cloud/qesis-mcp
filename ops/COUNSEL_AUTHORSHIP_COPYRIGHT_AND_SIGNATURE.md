# COUNSEL: authorship, copyright and the signature convention

**Prepared 2026-08-26 by COUNSEL on the operator's directive of the same date.
Status: sections 1 to 4 are analysis and bind nothing. Section 5 is applied.
Section 6 is drafted and NOT applied, and says why.**

**Authority.** CLAUDE.md section 1 (COUNSEL owns money and law, second opinion
behind SENTINEL on data licences), Rule SH-9 (an escalation without a
recommendation is an abdication), Rule SH-10g (counsel precedes compliance),
Rule R-1 (attribution is data, not blame), `LICENSE` sections 1 to 3.

**COUNSEL is not a lawyer.** This exists so that the operator's time with a
qualified professional is short and expensive in the right places. Nothing here
is legal advice and none of it should be relied on in a licence negotiation
without a solicitor or abogado confirming the position in the governing
jurisdiction.

---

## 1. The directive, restated precisely

The instruction was: everything produced in this session, although made by
Claude, belongs to the operator as the decision maker.

As an **operating instruction inside this ecosystem** that is unambiguous, it is
already how the repository behaves, and COUNSEL adopts it without qualification.
Every artefact this session produced was specified, directed and accepted by the
operator, and no agent holds or claims anything.

As a **statement of copyright law** it is not automatically true, and adopting
the loose version would weaken exactly the thing it is meant to protect. The
correction below makes the operator's position stronger rather than weaker,
which is why it is worth the paragraph.

## 2. What the law actually attaches to, and what it does not

**Copyright protects human authorship.** In the United States the Copyright
Office has refused registration for material with no human author, the D.C.
Circuit affirmed that position in *Thaler v. Perlmutter*, and the Supreme Court
declined to review it. A work containing machine-generated material is
registrable as to the **human contributions and the human selection and
arrangement**, and not as to the machine output standing alone.

In the European Union, including Spain, the standard is the **author's own
intellectual creation** (Infopaq, Painer, and TRLPI article 5, which requires a
natural person). Machine output with no human creative choice does not clear it.

The United Kingdom is the one jurisdiction with a computer-generated works
provision, CDPA section 9(3), vesting authorship in the person by whom the
arrangements necessary were undertaken, with a 50 year term and no moral rights.
It remains on the books and it remains under active review. **Do not build a
licensing position on section 9(3).** It is the weakest of the three and the
most likely to move.

**Consequence, stated plainly.** "Claude made it, therefore it is mine" is the
wrong sentence. The right sentence is:

> This repository is a human-authored work of Rodrigo Batista Silva that
> incorporates machine-assisted material. The protectable subject matter is the
> specification, the selection, the arrangement, the method and the data. The
> assistive runtime holds nothing and claims nothing.

That sentence survives an EU examiner, a US registration, a journal's
declaration form and an institutional licensee's diligence. The loose version
survives none of them, because it asserts a transfer of something that in most
of these jurisdictions never came into existence to be transferred.

**Where the transfer language does belong.** Whatever rights the model provider
does hold in outputs are dealt with by the terms of service between the operator
and that provider, not by a clause in this repository. That is a contract
question and it is already answered in the operator's favour by those terms; it
is not a copyright question and the two should not be run together in the same
sentence.

## 3. Three different things that keep being called authorship

| Question | Governed by | Answer here |
|---|---|---|
| Who owns the copyright | national copyright law | Rodrigo Batista Silva, as to the human-authored subject matter in section 2 |
| Who may be listed as an academic author | ICMJE, COPE and every major publisher's 2023 to 2025 AI policy | a natural person only. An AI system cannot be an author because it cannot take responsibility for the work. Disclose the assistance in the methods section |
| Who did what, in the record | this ecosystem's own doctrine, R-1 | recorded per artefact. Attribution is data, not blame, and it is not a claim of authorship |

The third one is the only one an agent may write. It is the signature convention
in section 5.

## 4. What was wrong in the record before this session

`qesis-mcp/AUTHORS.md` read, in full, that Rodrigo Batista Silva is a
**co-author**, and that the file was added to record co-authorship for the
changes in one branch, `fix/vercel-cache-headers`.

Two defects, neither fatal, both worth fixing before anything is deposited:

1. **"co-author" with no other author named.** A reader takes co-author to imply
   a second author. If that second author is understood to be the assistive
   runtime, the file is asserting the position section 2 says will not hold. If
   it is understood to be nobody, the word is simply wrong. The operator is the
   author.
2. **Scope tied to one branch.** An authorship file that describes one branch
   describes nothing about the work as it stands. `sovereign-infra` has no
   authorship file at all.

## 5. Applied this session: the signature convention

Applied because it is a documentation practice, reversible, and creates no
reliance by any third party. It is a **chain of custody line, not a claim of
authorship**, and that is stated in the block itself so it cannot be read as
one.

Every handover, decision record and session report closes with:

```
---
Decision holder: Rodrigo Batista Silva. Author for copyright purposes, and the
only signature on this record.
Prepared by: <runtime>, session of <date UTC>, acting under CLAUDE.md and
sovereign-infra/ops/GOVERNANCE.md. Machine attribution under R-1: data, not
authorship, and not a claim of any right.
Established from: <the commands and artefacts that produced the claims above>.
Landed by: <branch>, <commit>, merged by rebase under G-06 Rule 2-4.
```

The fourth line is left blank until the landing has happened and is filled from
the pull request, never from the intention. D-116 rule 1.

Applied to `ops/D-117_UNATTENDED_MEANS_LANDED.md` and to this session's report.

Also applied: `AUTHORS.md` is rewritten in `qesis-mcp` and created in
`sovereign-infra`, to the text in section 6.1, because it records attribution
rather than granting rights, and because leaving a file that says "co-author"
with no second author named is worse than any wording COUNSEL might get slightly
wrong.

## 6. Drafted and NOT applied, because the signature is the operator's

### 6.1 Applied, for the record: AUTHORS.md

See the file. It names the author, discloses the machine assistance, states that
no agent holds rights, and points at the licence split rather than restating it.

### 6.2 NOT applied: the LICENSE copyright line

`LICENSE` section 1 currently reads `Copyright (c) 2026 Rodrigo Batista Silva`
over the MIT grant, and section 2 places the index under CC BY-NC 4.0. Neither
is wrong. Both are silent on machine assistance, and a licensee's diligence will
ask. The proposed addition, for the operator's signature and not for an agent's:

> **Authorship and machine assistance.** This work is authored by Rodrigo
> Batista Silva. Parts of the code and documentation were produced with
> machine assistance under the author's direction and specification. The
> protectable subject matter claimed here is the specification, selection,
> arrangement, method and data. No automated system is an author of this work
> and none holds or claims any right in it. The grants in sections 1 and 2 are
> made by the author alone.

**Why COUNSEL does not apply this itself.** A licence file is the one document
in this repository that third parties rely on. Editing what a stranger may do
with the work is not a remediation and G-06 Rule 2-4 does not delegate it. It is
the same class of act as promotion: it publishes.

**What changes if the operator declines.** Nothing breaks. The current LICENSE
remains valid and internally consistent. The cost is that the first
institutional licensee, the first journal declaration, or an SSRN deposit will
raise the question and it will be answered under time pressure instead of now.

**What COUNSEL does the moment he decides.** On approval, the paragraph is added
as a new subsection of `LICENSE` between sections 2 and 3, `AUTHORS.md` gains a
line pointing at it, and both land in the same change set under G-01. On refusal,
this section is marked declined with the date and no further action is taken.

## 7. One thing COUNSEL will not pretend is settled

Whether machine-assisted material inside a larger human-authored work needs to
be **identified line by line** on a US registration, or whether a general
disclosure of assistance suffices, is not settled and the guidance has moved
twice. For a thesis and an SSRN deposit the general disclosure is the normal
practice today. For a registration filed to support an infringement claim, ask a
professional first. Confidence: moderate. Stating the tension is worth more than
a confident answer that ages badly.

---
Decision holder: Rodrigo Batista Silva. Author for copyright purposes, and the
only signature on this record.
Prepared by: Claude, Cowork session of 2026-08-26, acting under CLAUDE.md and
sovereign-infra/ops/GOVERNANCE.md. Machine attribution under R-1: data, not
authorship, and not a claim of any right.
Established from: LICENSE sections 1 to 3 as committed; AUTHORS.md as committed
before this session; the absence of any authorship file in sovereign-infra,
measured by directory listing; public sources on the human authorship
requirement current at 2026-08-26.
Landed by: pending.
