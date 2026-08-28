# G-09: an agent executes a deployment the human has already authorised

**Status: ADOPTED 2026-08-28 on the operator's direct instruction. Amends the
reading of G-03, G-04 and G-06 without weakening any of them.**

---

## 1. The rule

An agent **may execute** a deployment, a push or a promotion **when the human
operator has already made the authorising decision**. The agent acts as executor,
not as decision-maker. Prior authorisation is not a licence to decide; it is an
instruction to carry out a decision already taken.

An agent **may not** manufacture the authorisation, infer it from silence, or
treat a general expression of trust as authorisation for a specific act. The
authorisation names the act.

## 2. What this changes, and what it does not

**It changes the reading of G-06.** Promotion was previously described as a human
act in itself. It is now understood as a human **decision** whose **execution** an
agent may perform. The decision remains the operator's and no agent signs it.

**It does not change G-03 or G-04, and cannot.** Those clauses say no credential
moves in either direction. That is not a permission rule, it is a containment rule,
and authorisation does not transfer a secret. An agent with full authorisation and
no credential still cannot push.

## 3. The distinction that has to be kept, because conflating it wastes the rule

There are two different reasons an agent might not do something.

**Authority.** The agent is capable and not permitted. G-09 removes this obstacle
where the operator has authorised the act.

**Capability.** The agent is permitted and not able. G-09 does not touch this and
cannot, because a rule does not create a credential or a filesystem.

The authenticated push sits in the second category, for two measured reasons.
The GitHub credential is the operator's and lives in his `gh` configuration, which
no agent reads. And this runtime executes on a zero-trust analysis mount that
cannot unlink inside `.git`, so any git command it issues strands the index lock
and manufactures the blocker it would then report (L-122, L-123, L-150).

**Therefore: after G-09, the operator's double-click is still required for a push,
and the reason is now correctly stated.** It is not that an agent is forbidden. It
is that the credential and the working filesystem are on his machine and not on the
agent's.

## 4. The mechanism that already implements G-09

`LAND_EVERYTHING_FINAL.bat` is the executor and has been since revision 6. Under
it, the agent prepares the branch, stages, commits, writes the messages from the
manifest, opens the pull request, waits for the required check and merges by
rebase. The human contributes one double-click, which supplies the credential and
the filesystem.

That is exactly the division G-09 describes. What G-09 changes is the **wording of
the reports**: an act inside the lander is no longer marked as the operator's work.
It is the agent's work, executed through his session. Marking it `[RICO]` is a
defect in the report, and SH-10d already said so.

## 5. What is still, and permanently, his

G-09 leaves three things untouched, and they are the only three:

1. **Article 14 signatures.** A decision on the register is signed by a person or
   it is not signed.
2. **Credential material in either direction.** G-03 and G-04, unamended.
3. **A cost commitment.** Spending his money is his act.

Everything else an agent may do, it does. Where it cannot, it says which of the
two obstacles applies, authority or capability, and never presents the second as
the first.

## 6. Applied

`QT-0012`, the vault push, was closed on measurement the same day rather than
handed back. The vault repository holds one file, a README, and the bundle the
task described was not on disk. Had a bundle existed, the push would have been an
agent act under this clause and would have needed no further decision.
