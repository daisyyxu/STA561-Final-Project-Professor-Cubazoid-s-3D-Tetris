# Test case visualisations

Every case in `test_suite.py`, with its input pieces and (if solved)
an animated construction.  Open the PNGs and GIFs in a file browser.

## `01_2x2x2_two_tetracubes`

- **Status**: `solved`
- **Notes**: Two complementary tetracubes forming a 2x2x2.
- **Input preview**: `previews/01_2x2x2_two_tetracubes.png`
- **Construction animation**: `gifs/01_2x2x2_two_tetracubes.gif`

## `02_2x2x2_penta_plus_tri`

- **Status**: `solved`
- **Notes**: 2x2x2 split as 5 + 3 cubes.
- **Input preview**: `previews/02_2x2x2_penta_plus_tri.png`
- **Construction animation**: `gifs/02_2x2x2_penta_plus_tri.gif`

## `03_3x3x3_random_partition_s42`

- **Status**: `solved`
- **Notes**: Randomly-generated 3x3x3 partition (seed=42); mixed piece sizes.
- **Input preview**: `previews/03_3x3x3_random_partition_s42.png`
- **Construction animation**: `gifs/03_3x3x3_random_partition_s42.gif`

## `04_3x3x3_soma`

- **Status**: `solved`
- **Notes**: Classical 7-piece Soma cube.
- **Input preview**: `previews/04_3x3x3_soma.png`
- **Construction animation**: `gifs/04_3x3x3_soma.gif`

## `05_3x3x3_random_partition_s0`

- **Status**: `solved`
- **Notes**: Randomly-generated 3x3x3 partition (seed=0).
- **Input preview**: `previews/05_3x3x3_random_partition_s0.png`
- **Construction animation**: `gifs/05_3x3x3_random_partition_s0.gif`

## `06_3x3x3_random_partition_s7`

- **Status**: `solved`
- **Notes**: Randomly-generated 3x3x3 partition (seed=7).
- **Input preview**: `previews/06_3x3x3_random_partition_s7.png`
- **Construction animation**: `gifs/06_3x3x3_random_partition_s7.gif`

## `07_4x4x4_random_partition_s5`

- **Status**: `solved`
- **Notes**: Randomly-generated 4x4x4 partition (seed=5); mixed piece sizes.
- **Input preview**: `previews/07_4x4x4_random_partition_s5.png`
- **Construction animation**: `gifs/07_4x4x4_random_partition_s5.gif`

## `08_4x4x4_sixteen_L_tetracubes`

- **Status**: `solved`
- **Notes**: Sixteen flat L-tetracubes — classic tiling.
- **Input preview**: `previews/08_4x4x4_sixteen_L_tetracubes.png`
- **Construction animation**: `gifs/08_4x4x4_sixteen_L_tetracubes.gif`

## `09_4x4x4_sixteen_T_tetracubes`

- **Status**: `solved`
- **Notes**: Sixteen flat T-tetracubes (four per 4x4x1 slab).
- **Input preview**: `previews/09_4x4x4_sixteen_T_tetracubes.png`
- **Construction animation**: `gifs/09_4x4x4_sixteen_T_tetracubes.gif`

## `10_4x4x4_sixteen_O_tetracubes`

- **Status**: `solved`
- **Notes**: Sixteen 2x2x1 squares.
- **Input preview**: `previews/10_4x4x4_sixteen_O_tetracubes.png`
- **Construction animation**: `gifs/10_4x4x4_sixteen_O_tetracubes.gif`

## `11_4x4x4_mixed_LTS`

- **Status**: `parity_rejected`
- **Notes**: Sixteen mixed flat tetracubes (6 L + 5 T + 5 S) — parity infeasible.
- **Input preview**: `previews/11_4x4x4_mixed_LTS.png`

## `12_4x4x4_random_partition_s1`

- **Status**: `solved`
- **Notes**: Randomly-generated 4x4x4 partition (seed=1).
- **Input preview**: `previews/12_4x4x4_random_partition_s1.png`
- **Construction animation**: `gifs/12_4x4x4_random_partition_s1.gif`

## `13_4x4x4_random_partition_s3`

- **Status**: `solved`
- **Notes**: Randomly-generated 4x4x4 partition (seed=3).
- **Input preview**: `previews/13_4x4x4_random_partition_s3.png`
- **Construction animation**: `gifs/13_4x4x4_random_partition_s3.gif`

## `14_5x5x5_random_partition_s11`

- **Status**: `solved`
- **Notes**: Randomly-generated 5x5x5 partition (seed=11); mixed piece sizes.
- **Input preview**: `previews/14_5x5x5_random_partition_s11.png`
- **Construction animation**: `gifs/14_5x5x5_random_partition_s11.gif`

## `15_5x5x5_random_partition_s0`

- **Status**: `solved`
- **Notes**: Randomly-generated 5x5x5 partition (seed=0).
- **Input preview**: `previews/15_5x5x5_random_partition_s0.png`
- **Construction animation**: `gifs/15_5x5x5_random_partition_s0.gif`

## `16_5x5x5_random_partition_s2`

- **Status**: `solved`
- **Notes**: Randomly-generated 5x5x5 partition (seed=2).
- **Input preview**: `previews/16_5x5x5_random_partition_s2.png`
- **Construction animation**: `gifs/16_5x5x5_random_partition_s2.gif`

## `17_invalid_volume_not_cube`

- **Status**: `invalid_volume`
- **Notes**: Total volume is 7 — not a perfect cube.
- **Input preview**: `previews/17_invalid_volume_not_cube.png`

## `18_no_solution_wrong_shapes_2x2x2`

- **Status**: `no_solution`
- **Notes**: Two flat L-tetracubes can't tile a 2x2x2 (need 3D footprint).
- **Input preview**: `previews/18_no_solution_wrong_shapes_2x2x2.png`

## `19_no_solution_I5s_in_3x3x3`

- **Status**: `no_solution`
- **Notes**: Volume 27 passes (3×5 + 3×4), but length-5 rods cannot fit in a 3-cube.
- **Input preview**: `previews/19_no_solution_I5s_in_3x3x3.png`

## `20_invalid_disconnected_piece`

- **Status**: `invalid_input`
- **Notes**: Piece has two disconnected cells.
- **Input preview**: `previews/20_invalid_disconnected_piece.png`

## `21_invalid_empty_list`

- **Status**: `invalid_input`
- **Notes**: Empty piece list.
- **Input preview**: `previews/21_invalid_empty_list.png`

## `22_invalid_non_binary`

- **Status**: `invalid_input`
- **Notes**: Piece tensor has a value != 0/1.
- **Input preview**: `previews/22_invalid_non_binary.png`

## `23_invalid_not_3d`

- **Status**: `invalid_input`
- **Notes**: Piece is a 2D tensor, not 3D.
- **Input preview**: `previews/23_invalid_not_3d.png`

## `24_4x4x4_random_partition_s17`

- **Status**: `solved`
- **Notes**: Randomly-generated 4x4x4 partition (seed=17); another diverse mix.
- **Input preview**: `previews/24_4x4x4_random_partition_s17.png`
- **Construction animation**: `gifs/24_4x4x4_random_partition_s17.gif`

## `25_3x3x3_mixed_pentatri`

- **Status**: `solved`
- **Notes**: 3x3x3 partitioned with mixed tri/tetra/pentacubes.
- **Input preview**: `previews/25_3x3x3_mixed_pentatri.png`
- **Construction animation**: `gifs/25_3x3x3_mixed_pentatri.gif`

