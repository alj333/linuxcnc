# Head-Head Fusion Postprocessor Requirements

This note defines the software requirements for the Fusion postprocessor that
will target the current head-head TCPC/TWP controller contract.

It is written against the actual local Fusion post baselines on this PC:

- `/home/cnc5/Fusion/linuxcnc(1).cps`
- `/home/cnc5/Fusion/fanuc(1).cps`
- `/home/cnc5/Fusion/fanuc inspection(1).cps`

## Primary Decision

Recommended starting point:

- milling post base:
  - `fanuc(1).cps`
- inspection/probing post base:
  - `fanuc inspection(1).cps`
- LinuxCNC post use:
  - keep `linuxcnc(1).cps` as a reference for LinuxCNC-friendly file style,
    extension, and simple baseline behavior
  - do not use it as the main 5-axis base

Reason:

- the local LinuxCNC Fusion post currently advertises:
  - `useTiltedWorkplane: false`
  - `supportsTCP: false`
- the local Fanuc and Fanuc inspection posts already carry:
  - tilted workplane support (`G68.2`-style intent)
  - TCP/TWP state handling concepts
  - Renishaw-style probing/inspection support
  - multi-feature inspection result handling

For this machine, 5-axis behavior and inspection support matter more than
keeping the generic LinuxCNC post structure.

## Machine-Facing Contract

The post must target the current controller contract in:

- [fanuc_like_twp_tcpc_contract.md](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/fanuc_like_twp_tcpc_contract.md)

Current machine-facing modes:

- `G43.4` = TCPC on
- `G49.1` = TCPC off
- `G68.2 [B.. C..] [R..]` = define and activate TWP
- `G69` = cancel TWP

Required behavioral assumption:

- ordinary `G0/G1 X/Y/Z` are used while TWP is active
- the post must not pre-transform every move into machine coordinates
- the post must not target the old `G88.5` debug path

## Post Family Recommendation

Use two related posts, not one overloaded post:

1. `Head-Head Fanuc-Like Mill`
2. `Head-Head Fanuc-Like Inspection`

Reason:

- the milling workflow and inspection workflow have different output needs
- the inspection path will likely need result-file logic and probing-cycle
  control that should not clutter the normal milling post
- both can still share the same controller contract and common helpers

## Milling Post Requirements

### Program Format

Required:

- ISO G-code output
- metric-first workflow
- absolute programming
- standard milling preamble compatible with LinuxCNC
- LinuxCNC-friendly extension:
  - prefer `.ngc`
- optional sequence numbers
- comments allowed but not required

Acceptable:

- Fanuc-like block style
- LinuxCNC-style file extension and some startup/cancel details

### Motion Model

Required:

- 3-axis jobs output as ordinary LinuxCNC-compatible milling code
- indexed 3+2 and 5-axis jobs target the machine TCPC/TWP contract
- posted 5-axis motion must assume:
  - TCPC on before tilted-plane motion
  - TWP active during local-plane linear motion
  - explicit cancel before tool change, tool-state change, and end of program

### TCPC / TWP Output Rules

Required:

- output `G43.4` before any posted TCPC-dependent or TWP-dependent motion
- output `G68.2 B.. C.. [R..]` when entering a tilted workplane
- output ordinary `G0/G1 X/Y/Z` while TWP is active
- output `G69` before any change of tool state or exit from TWP mode
- output `G49.1` when explicitly leaving TCPC mode

Required cancel order before tool change:

1. `G69`
2. `G49.1`
3. tool change / tool-length state change

### Rotary Handling

Required:

- allow manual/indexed `B/C` positioning only while TWP is off
- when the post wants a new tilted plane, it must emit the desired `B/C` in the
  `G68.2` block rather than relying on hidden machine state
- do not output changing `B/C` words during active TWP linear motion

### Arc / Cycle Rules

Required first production assumption:

- avoid relying on arcs in active TWP until proven on the real machine
- linearize or otherwise avoid unsupported 5-axis/TWP arc paths if needed
- treat canned cycles in active TWP as unsupported until explicitly validated

This should be a post property or enforced behavior, not left ambiguous.

### Tool / TLO Rules

Required:

- never emit `G43`, `G43.1`, `G43.2`, `G49`, `M6`, or `M61` while TWP is active
- any tool-length state change must happen only after `G69`
- if the post uses `G43 H...` for ordinary tool length, it must remain coherent
  with the machine rule that `G43.4` is TCPC mode

This needs careful implementation because the machine uses LinuxCNC internals
with a Fanuc-like external contract.

### Safe Retract / End Of Program

Required:

- all end-of-operation retract logic must be explicit and predictable
- before major retracts, tool changes, or program end:
  - cancel TWP with `G69`
  - cancel TCPC with `G49.1` when needed
- avoid hidden mode carryover between operations

## Inspection Post Requirements

### Base Recommendation

Start from:

- `/home/cnc5/Fusion/fanuc inspection(1).cps`

Reason:

- it already contains probing and inspection infrastructure
- it already carries G68.2-style tilted workplane intent
- it already includes result-file handling and multi-feature inspection support

### Inspection Scope

Required inspection capability:

- standard probe qualification / inspection toolpaths
- indexed probing at rotary poses needed for mold work
- surface probing / point-cloud style probing where Fusion inspection supports it
- output of measured results in a form that can be fed back to Fusion for mold
  alignment work

### Mold Alignment Requirement

The inspection post must support the workflow:

1. probe the real mold or reference surface
2. capture measured offsets / orientation error
3. export results in a Fusion-consumable or Fusion-workflow-compatible format
4. allow the programmer to realign the CAM setup from measured data

This is a primary requirement, not a nice-to-have.

### Probing Motion Rules

Required:

- probing should default to world or indexed frames, not active TWP motion,
  unless TWP probing is explicitly validated later
- do not probe while unsupported rotation compensation modes are active
- use explicit mode transitions around probing sections
- keep probing output conservative and easy to diagnose

### Inspection Results

Required:

- output measurable results to file, not just operator messages
- support multi-feature inspection in a single job
- preserve enough context to map results back to Fusion features/setup

Preferred:

- one predictable results-file convention for this machine
- easy operator retrieval from LinuxCNC

## LinuxCNC-Specific Adaptation Requirements

Even though the Fanuc-family posts are the better base, the final post must be
adapted to LinuxCNC realities:

- file extension should be LinuxCNC-friendly
- startup and cancel code must match the head-head controller contract
- simple M-code behavior should stay minimal
- avoid Fanuc features the controller does not implement
- keep generated code readable to staff already familiar with Fanuc-style 5-axis

## Deliberate Simplifications

The machine is intentionally simple. The post should not invent complexity.

Assume:

- minimal custom M-codes
- no heavy ATC-specific logic in the first production post
- no dependency on obscure Fanuc-only modal features unless they are truly
  required

## Required Post Properties

At minimum, expose properties for:

- sequence numbers on/off
- safe retract style
- optional stop behavior
- linearization of unsupported TWP arcs/cycles
- output extension (`.ngc` preferred)
- inspection results file behavior
- whether to emit explicit TCPC off at program end

## Validation Requirements For The Post

Before the post is treated as usable, validate:

1. simple 3-axis program
2. indexed 3+2 program
3. TCPC-only 5-axis motion
4. TWP-based 5-axis motion
5. inspection/probing output
6. mold-alignment probing result export path

Validation should use the machine-facing references already in this repo:

- [machine_bringup_checklist.md](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_bringup_checklist.md)
- [machine_tcp_twp_verification_sequence.md](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/machine_tcp_twp_verification_sequence.md)
- [software_acceptance_matrix.md](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/software_acceptance_matrix.md)

## First Build Recommendation

Build order:

1. fork the Fanuc milling post for the head-head milling contract
2. fork the Fanuc inspection post for the head-head inspection contract
3. pull only the LinuxCNC-specific file/startup conventions that are actually
   needed
4. validate the milling post against the sim and machine contract first
5. validate the inspection/mold-alignment workflow second

This is the lowest-risk path for this machine.
