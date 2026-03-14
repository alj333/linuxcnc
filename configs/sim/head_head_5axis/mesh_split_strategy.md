# STEP Split Strategy

## Purpose

This note maps the uploaded STEP assembly into the moving groups required for a
future articulated head-head visual simulation.

It answers two questions:

1. what can be derived from the current STEP export
2. what extra CAD exports are still required

## Source Files

Current source material:

- STEP assembly:
  - `/home/cnc5/dev/5thAxis/5th_Axis.step`
- screenshots:
  - `/home/cnc5/dev/5thAxis/Screenshot 2026-03-14 173108.png`
  - `/home/cnc5/dev/5thAxis/Screenshot 2026-03-14 173147.png`
  - `/home/cnc5/dev/5thAxis/Screenshot 2026-03-14 173209.png`

## Current STEP Product Inventory

Top-level product names seen in the STEP file:

- `BaseFrame`
- `CrossBeam`
- `X Axis Frame`
- `X Axis Rail`
- `Z-Axis Frame`
- `Z-Axis Rail`
- `Head`
- `Spindle`
- `Table`
- `Y Axis Rail`
- plus bearings, supports, and drive/support hardware

Reference copy:

- [step_product_inventory.txt](/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/step_product_inventory.txt)

## Simulation Groups We Actually Need

For a proper articulated head-head machine simulation, the visual model should
be split into at least these groups:

1. fixed base group
2. Y-moving gantry group
3. X-moving carriage group
4. Z-moving carriage group
5. C-axis rotating group
6. B-axis rotating group
7. spindle/tool group

## Proposed Mapping From Current Assembly

### 1. Fixed Base Group

Likely members:

- `BaseFrame`
- `Table`
- fixed supports and non-moving structure

This group should not move in the visual simulation.

### 2. Y-Moving Gantry Group

Likely members:

- `CrossBeam`
- any side supports that are mechanically part of the gantry and travel in `Y`

This group should translate in `Y`.

### 3. X-Moving Carriage Group

Likely members:

- `X Axis Frame`

This group should translate in `X` relative to the gantry.

### 4. Z-Moving Carriage Group

Likely members:

- `Z-Axis Frame`

This group should translate in `Z` relative to the X carriage.

### 5. C-Axis Rotating Group

Desired members:

- C rotary housing/body
- all downstream geometry except pieces that rotate further on B

Problem:

- the current STEP inventory does not expose a separate `C` body/product
- the closest visible group is `Head`, which appears to combine more than one
  rotary stage from the screenshots

### 6. B-Axis Rotating Group

Desired members:

- B tilt stage
- spindle mount
- downstream spindle/tool geometry

Problem:

- the current STEP inventory does not expose a separate `B` body/product
- `Head` appears to include both rotary stages as one product

### 7. Spindle/Tool Group

Likely members:

- `Spindle`

This is separable in the current STEP inventory.

## Key Limitation In Current STEP Export

The current assembly appears to be too coarse for direct articulated `B/C`
visualization because:

- `Head` is a single product
- there is no explicit product for the `C` stage alone
- there is no explicit product for the `B` stage alone

So the current export is good enough for:

- full machine static mesh
- rough visual reference
- planning the group hierarchy

But it is not yet good enough for:

- a proper articulated `C` rotation
- a proper articulated `B` tilt

## Required Next CAD Exports

To build a real articulated visual simulation, the next CAD export should
separate at least these bodies or subassemblies:

1. fixed base/table
2. Y gantry
3. X carriage
4. Z carriage
5. C-axis body
6. B-axis body
7. spindle

Preferred export format:

- STL per moving group for the first visual simulation

Better long-term option:

- one STEP or Fusion model with named subassemblies that already reflect the
  simulation group hierarchy

## Practical Recommendation

Do not spend time trying to infer the `B` and `C` split from the current full
assembly export.

Instead:

1. keep the full mesh for whole-machine reference
2. request/export separate meshes for:
   - base
   - gantry
   - X carriage
   - Z carriage
   - C body
   - B body
   - spindle
3. then build the visual kinematic chain around those exports

## Immediate Next Step

The software side can proceed in parallel:

- continue the math-only kinematics work using the agreed geometry baseline
- prepare the visual sim hierarchy

The CAD side should provide the split moving groups listed above.
