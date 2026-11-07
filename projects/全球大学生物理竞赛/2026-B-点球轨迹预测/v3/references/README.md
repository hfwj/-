# 物理来源与参数状态

- [题目：2026 UPC Problem B](https://university-physics-competition.com/2026-competition)：坐标、球门平面和初始球心高度。
- [IFAB Law 2](https://www.theifab.com/laws/latest/the-ball/)：比赛开始时质量范围410～450 g；本版本基准设0.43 kg。
- [Kray et al. (2014), Magnus effect on a rotating soccer ball at high Reynolds numbers](https://doi.org/10.1016/j.jweia.2013.10.010)：旋转足球的气动力系数依赖流动和自旋条件，经验系数需要匹配数据。
- [Asai & Hong (2021), football wind-tunnel study](https://pmc.ncbi.nlm.nih.gov/articles/PMC8100144/)：球型、表面和朝向影响阻力曲线。不能仅凭某个Re值认定未知球型必在阻力危机区。
- [Mizota et al. (2013), slowly spinning soccer balls](https://pmc.ncbi.nlm.nih.gov/articles/PMC3660809/)：非定常侧向气动力的实验动机；不直接证明OU闭合及本版本的扰动参数适用于题目样例。

本版本没有从这些论文数字化气动曲线；默认Cd、升力斜率、自旋衰减率和OU参数均为清楚标注的演示输入。表格气动接口供后续导入有来源的数据。

用户上传的两份深化/评估文档仅作为待审阅参考；其“已校准”“一定处于阻力危机区”及速度因子等结论未直接作为本模型前提。
