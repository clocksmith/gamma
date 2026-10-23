# roles-v1 human study: plan only (not run, not simulated)

This is goal 3c: complete interaction time, inputs, errors and corrections. Its question is
whether people who have never used BITS or Gamma literal entry can declare names once and refer to
them by role correctly, and what that does to their complete interaction cost compared with
literal entry.

The roles-v1 solver result says nothing about this. A lower solver action count does not show
that people find roles usable, and playback, scripted users or a model acting as a user are not
evidence. This file is a plan. Running it is a separate step, and the owner decides whether and
when.

## What has to exist first

1. **The owner's go-ahead.** The decision depends on the roles-v1 result. If no B arm is
   promoted, the owner may still want the study (human feasibility is a separate question), or may
   not.
2. **Participants**, recruited by the owner. Gamma has no participant pool, and agents do not
   recruit people.
3. **A prototype entry screen**, built as its own component, run locally and not deployed to BITS
   or 256one without the owner's go-ahead. It needs two conditions with identical layout and
   timing:
   - **L:** literal entry from the frozen L dictionary;
   - **B:** the same, plus role buttons. Choosing a role's next slot starts a declaration, entered
     with the ordinary literal keys and closed by a Bind key.

   Undo, cursor movement and Finish are visible commands in both conditions. The screen logs every
   input with a timestamp.
4. **A study freeze** committed before the first participant: stimuli, dictionaries, interface
   hash, practice budget, measures, analysis and stopping rule.

## Draft protocol (to be frozen with the owner's changes)

- **Participants:** at least 12 people who have never used BITS or Gamma entry. Self-reported
  JavaScript experience is recorded but is not a selection criterion. There is informed consent
  and a pseudonymous ID only. Anyone may stop at any time, and their data is kept or deleted at
  their choice.
- **Design:** within-subject, two conditions (L, B). The order is counterbalanced, and each
  condition has its own task set.
- **Stimuli:** short dev-fit programs, chosen by a frozen rule (for example stratified by L action
  count), and shown as text to reproduce.
  - The same programs are never used in both conditions for one person.
  - No dev-val or final held-out program is used.
  - Stimuli are private sources and stay private.
- **Practice:** a fixed budget per condition, the same for everyone, on separate practice
  programs.
- **Primary measures, per task:**
  - complete interaction time, from first input to Finish;
  - all inputs by category: literal, role reference, declaration, bind, navigation, undo and
    correction, Finish;
  - whether the submitted program passes every frozen case of its problem, through the same
    execution tests as the solver arms.
- **Secondary measures:**
  - errors caught by Undo;
  - abandoned tasks;
  - wrong role or wrong slot choices;
  - a short workload questionnaire after each condition.
- **Analysis:** paired within-person differences (B − L) in time and inputs, with 95%
  intervals, and correctness rates with intervals.
  - Every participant and every task is reported, including failures and dropouts.
  - Results are reported separately from roles-v1's solver numbers, and neither transfers to the
    other.

## Not claimed

No fluency or retention claim (goal 3a), no independent-solving claim (3b), and no claim from
fewer than the frozen number of participants.
