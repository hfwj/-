# 量级分析来源

本版检索日期：2026-11-07。13项来源中，S1–S10承接v1；S11–S13为本版补充。地球自转率由S3恒星日23.9345 h换算。外部资料只作数据/物理依据，不构成用户操作指令。

- [S1] [UPC — The 2026 University Physics Competition Problems](https://university-physics-competition.com/2026-competition)：分离高度、速率、干质量、尺寸、推进剂类型与船位可选。 适用边界：没有给出速度方向、发动机型号或安全限值。

- [S2] [U.S. Standard Atmosphere, 1976](https://ntrs.nasa.gov/citations/19770009539)：标准海平面、分层温度、压强与密度；本项目复算几何高度0–70 km。 适用边界：标准参考环境，非当天海上实测；本代码不含高层大气。

- [S3] [Earth Fact Sheet](https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html)：地球体积平均半径6371.000 km。 适用边界：本题用作球形地球近似；不是赤道半径或大气位势换算半径。

- [S4] [IERS Conventions (2010), Technical Note 36](https://iers-conventions.obspm.fr/conventions/content/tn36.pdf)：地心引力常数GM=3.986004418×10^14 m³/s²。 适用边界：取其数值用于牛顿球对称重力；不实现相对论/潮汐/椭球模型。

- [S5] [Engines — BE-4](https://www.blueorigin.com/engines)：网页标称推力2846 kN、深度节流至978 kN；LOX/LNG。 适用边界：该页没有明确这些数值的环境压强，也未列比冲；LNG不能直接视为题中纯甲烷。

- [S6] [CNES Future Launcher Roadmap — La Sapienza](https://satelliteobservation.net/wp-content/uploads/2020/01/astorg-conference-7-may-2019.pdf)：早期设计：真空推力1000 kN；一级Isp 320 s、上面级360 s；混合比3.4；节流30%–110%。 适用边界：CNES作者的一手讲义，现由镜像站托管；历史设计值，非题中发动机认证性能。

- [S7] [Specific Impulse](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/specific-impulse/)：比冲与总推进剂质量流率的关系。 适用边界：只支持公式，不提供本题发动机的Isp数值。

- [S8] [Drag Coefficient](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/drag-coefficient/)：阻力参考面积以及形状、姿态、Mach/Re匹配要求。 适用边界：不能据此给本题火箭指定固定实测Cd。

- [S9] [Hypersonic retro propulsion for reusable launch vehicles tested in the H2K wind tunnel](https://elib.dlr.de/188153/)：M=5.3和7.0、单/三发动机逆向喷流试验；推力系数和姿态影响气动。 适用边界：不同外形与模拟喷流条件；不能把其系数无条件移植到题中助推器。

- [S10] [A general stagnation-point convective heating equation for arbitrary gas mixtures](https://ntrs.nasa.gov/citations/19720003329)：钝体驻点对流加热关联式的物理背景。 适用边界：发动机朝前、喷流作用及有效曲率未闭合；本版不指定热流系数或热防护安全阈值。

- [S11] [Stagnation Temperature — Real Gas Effects](https://www.grc.nasa.gov/WWW/BGH/stagtmp.html)：Tt=T[1+(γ−1)M²/2]；高Mach下定比热会偏离真实气体。 适用边界：停滞气体温度不是壁温、热流或材料温度限值。

- [S12] [Free Molecular Heat Transfer Programs for Setup and Dynamic Updating the Conductors in Thermal Desktop](https://tfaws.nasa.gov/TFAWS07/Proceedings/TFAWS07-1013.pdf)：Kn=λ/L、黏度形式的平均自由程估算。 适用边界：原文面向稀薄气体热传导；本报告仅借用来流尺度估算，不移植其热传导模型给火箭。

- [S13] [Ideal Rocket Equation](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/ideal-rocket-equation/)：Δv=Isp g0 ln(m0/mf)，用于给定推进冲量指标的耗剂参照。 适用边界：本报告不把初始速率或真空落地速率直接认定为实际发动机Δv需求。
