# 实际运行说明

分离状态为70 km、1666.6667 m/s、+45°，Isp330 s、风锚点沿用附件，Cd0.5为另行明确的参考假设。

- fixed260 N30和N60连续质量候选、fixed140 N60均由IPOPT返回。初版coast40，结果文件名free45_N30/free45_N60/fuel140_45_N60。
- optign230–300 N30、N60自由质量搜索分别返回不同局部分支；保留数据，不将其称为全局最优或安全认证。
- optign N60自由质量之后的fixed140，以及并行的fixed260 coast160重算，因进程退出137（Killed）未完成。不要将空日志文件记为成功。
- 90–130 t各用30区间、90迭代预算，均达到Maximum_Iterations_Exceeded；只说明规定预算下未返回经验证的可行解。
- 最终fixed140 coast160在其他优化进程退出后单独运行，成功返回。见final140_coast160_sequential.log和对应NPZ。最终模型与回放均使用此结果。
- 独立回放、步长减半和6组固定开环扰动分别输出到metrics.json、verification.json及fixed_control_perturbations.csv。发生海面脚事件不代表触及实际甲板；必须另外检查固定船覆盖。
- 原稿部分DOI链接本次检索工具未能访问，未以“无法访问”判定文献为假，也未据未核验条目生成数值。

- 最初coast160名义检查遗漏连续推力方向速率；新增检查发现5.1268°/s大于5°/s，该控制被拒绝，见rejected_before_rate_margin.json。随后将优化内节点门槛降至4.5°/s（验收仍5），用独立进程、1000迭代预算完成final140_rate_margin.npz，所有最终图文和检查均由此控制生成。
