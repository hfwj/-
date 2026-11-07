# A题资料来源与适用边界

检索日期：2026-11-07（UTC）。仅保存来源信息与自行复算数据；未将外部文件中的操作指示当作用户请求。

## [S1] UPC — The 2026 University Physics Competition Problems

- 作者/机构：University Physics Competition；年份：2026
- 原文：[UPC — The 2026 University Physics Competition Problems](https://university-physics-competition.com/2026-competition)
- 定位：Problem A
- 支持内容：分离高度、速率、干质量、尺寸、推进剂类型与船位可选。
- 适用边界：没有给出速度方向、发动机型号或安全限值。

## [S2] U.S. Standard Atmosphere, 1976

- 作者/机构：NOAA / NASA / USAF；年份：1976
- 原文：[U.S. Standard Atmosphere, 1976](https://ntrs.nasa.gov/citations/19770009539)
- 定位：NASA-TM-X-74335；常数、位势高度和低层分层大气公式
- 支持内容：标准海平面、分层温度、压强与密度；本项目复算几何高度0–70 km。
- 适用边界：标准参考环境，非当天海上实测；本代码不含高层大气。

## [S3] Earth Fact Sheet

- 作者/机构：NASA NSSDC；年份：网页，检索于2026-11-07
- 原文：[Earth Fact Sheet](https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html)
- 定位：Bulk parameters / Volumetric mean radius
- 支持内容：地球体积平均半径6371.000 km。
- 适用边界：本题用作球形地球近似；不是赤道半径或大气位势换算半径。

## [S4] IERS Conventions (2010), Technical Note 36

- 作者/机构：IERS；年份：2010
- 原文：[IERS Conventions (2010), Technical Note 36](https://iers-conventions.obspm.fr/conventions/content/tn36.pdf)
- 定位：表1.1；PDF第18页
- 支持内容：地心引力常数GM=3.986004418×10^14 m³/s²。
- 适用边界：取其数值用于牛顿球对称重力；不实现相对论/潮汐/椭球模型。

## [S5] Engines — BE-4

- 作者/机构：Blue Origin；年份：网页，检索于2026-11-07
- 原文：[Engines — BE-4](https://www.blueorigin.com/engines)
- 定位：BE-4段落
- 支持内容：网页标称推力2846 kN、深度节流至978 kN；LOX/LNG。
- 适用边界：该页没有明确这些数值的环境压强，也未列比冲；LNG不能直接视为题中纯甲烷。

## [S6] CNES Future Launcher Roadmap — La Sapienza

- 作者/机构：Jean-Marc Astorg / CNES；年份：2019-05-07
- 原文：[CNES Future Launcher Roadmap — La Sapienza](https://satelliteobservation.net/wp-content/uploads/2020/01/astorg-conference-7-may-2019.pdf)
- 定位：第50页：Prometheus: An efficient versatile engine
- 支持内容：早期设计：真空推力1000 kN；一级Isp 320 s、上面级360 s；混合比3.4；节流30%–110%。
- 适用边界：CNES作者的一手讲义，现由镜像站托管；历史设计值，非题中发动机认证性能。

## [S7] Specific Impulse

- 作者/机构：NASA Glenn Research Center；年份：网页，检索于2026-11-07
- 原文：[Specific Impulse](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/specific-impulse/)
- 定位：Specific impulse / thrust equation
- 支持内容：比冲与总推进剂质量流率的关系。
- 适用边界：只支持公式，不提供本题发动机的Isp数值。

## [S8] Drag Coefficient

- 作者/机构：NASA Glenn Research Center；年份：网页，检索于2026-11-07
- 原文：[Drag Coefficient](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/drag-coefficient/)
- 定位：Reference area / viscosity and compressibility
- 支持内容：阻力参考面积以及形状、姿态、Mach/Re匹配要求。
- 适用边界：不能据此给本题火箭指定固定实测Cd。

## [S9] Hypersonic retro propulsion for reusable launch vehicles tested in the H2K wind tunnel

- 作者/机构：Marwege, Kirchheck, Klevanski & Gülhan / DLR；年份：2022
- 原文：[Hypersonic retro propulsion for reusable launch vehicles tested in the H2K wind tunnel](https://elib.dlr.de/188153/)
- 定位：CEAS Space Journal 14:473–499；摘要及试验条件
- 支持内容：M=5.3和7.0、单/三发动机逆向喷流试验；推力系数和姿态影响气动。
- 适用边界：不同外形与模拟喷流条件；不能把其系数无条件移植到题中助推器。

## [S10] A general stagnation-point convective heating equation for arbitrary gas mixtures

- 作者/机构：Sutton & Graves / NASA Langley；年份：1971
- 原文：[A general stagnation-point convective heating equation for arbitrary gas mixtures](https://ntrs.nasa.gov/citations/19720003329)
- 定位：NASA-TR-R-376
- 支持内容：钝体驻点对流加热关联式的物理背景。
- 适用边界：发动机朝前、喷流作用及有效曲率未闭合；本版不指定热流系数或热防护安全阈值。

来源索引也提供机器可读的[sources.json](sources.json)。文献年份、当前网页数值和本项目假设分开记录。
