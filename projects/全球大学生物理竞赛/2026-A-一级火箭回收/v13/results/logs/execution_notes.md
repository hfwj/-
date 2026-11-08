# 实际运行记录

- 连续候选free60：初始推进剂133.437273 t，仅作暖启动/量级参照。
- 90–130 t严格局部搜索：每次N=30、max_iter=90，均Maximum_Iterations_Exceeded；见low.log与low_search_history.json。不是不可行证明。
- 初始140 t：N=60，已收敛，但连续回放在229.56 m倾角5.3553°，拒绝；原控制单独保留rejected_140t_controls.npz。
- N=120重优化：进程退出137（Killed），没有收敛结果；不是网格收敛证据。
- 修订140 t：低空优化限制改3.5°，仍验收5°，N=60、max_iter=700，IPOPT成功；最终独立回放见metrics.json和verification.json。
- 最终图文均由修订控制生成；最终脚端事件的步长减半结果见metrics.json。
- CNES与EUCASS原PDF通过web检索工具阅读；直接下载遭网络代理403，未伪造存档。未申请额外权限；参数与来源网页保留。
