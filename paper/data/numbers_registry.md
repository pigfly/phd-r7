# Number registry (all paper numbers come from these files)

- table1_baselines_ruler16k <- analysis_ruler.json keys rbase_s{5,6}_*|<reader> (16K chars, N=25/task, 3 tasks)
- length_scaling <- analysis_ruler.json keys rlong_c{32,64,128}k_*|<reader> (6px, N=20/task)
- density_sweep <- analysis_ruler.json rdens_k*|<reader> (32K, N=25); routing <- analysis_routing.json
- longbench_lb3 (A/S/K/X, N=50/task) / lb2 (A/M/S/L) / lb_s6 (T/A/M, disjoint samples) <- analysis_longbench.json
- detector_ablation <- analysis_ruler.json rdet_mv{7,4}|<reader> (16K, N=25, 5 readers)
- real_density <- analysis_real_density.json
- claude_subagent <- analysis_claude_reader.json
- sweep_short (E2 phase diagram, short synthetic) <- analysis_sw_s5_sw_s6_sw_s8_sw_s10.json
