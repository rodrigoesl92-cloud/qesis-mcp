# DORA ROI & Agentic Stability Baseline (v8.6)

## 1. The Verification Tax & Guardrails
- AI acts as an amplifier, increasing both throughput and software delivery instability.
- Agents MUST route all generated code and data modifications through the 12 automated verification gates (verify_chain.py, verify_index.py) to mitigate the verification tax.

## 2. Experiment Frequency & Optionality
- Agents are authorized to maximize 'experiment frequency' by generating multiple configurations for fsQCA and IPE analysis.
- This lowers the option premium of testing new theories; however, options are only 'exercised' (promoted) upon passing the clean-room gates.

## 3. The Context Layer
- To prevent hallucination, agents must strictly reference the AI-accessible internal data housed in .claude/ and my-agent/.
- Original causal UX/UI design formulations take precedence over generic industry assumptions.

## 4. Navigating the J-Curve
- Systemic friction during initial multi-agent scaling is recognized as the J-Curve tuition cost.
- The primary metric for escaping the trough is maintaining zero link breaks in the cryptographic chain spine while increasing deployment throughput.
