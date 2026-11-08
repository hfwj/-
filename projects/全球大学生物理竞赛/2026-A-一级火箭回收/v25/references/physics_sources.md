# 参数与关系来源

- USSA 1976层结关系与标准大气常数：NOAA/NASA/USAF，NASA-TM-X-74335，https://ntrs.nasa.gov/citations/19770009539 。本模型86 km以上的指数延拓并非USSA高空完整模型，H=7000 m为明确假设，并测试5000/10000 m。
- 阻力关系、参考面积与Cd约定：NASA Glenn，https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/drag-equation/ 。12个Cd锚点是本研究H假设，不是该页面给出的火箭数据。
- 比冲与质量流率/推力关系：NASA Glenn，https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/specific-impulse/ 。Isp=330 s及单机1 MN、节流/迟滞参数为假设，未宣称某实机标定值。
- Powell搜索：原始方法论文DOI 10.1093/comjnl/7.2.155；SciPy当前接口与边界行为https://docs.scipy.org/doc/scipy/reference/optimize.minimize-powell.html 。
- 所有风节点、几何余量、控制参数及验收阈值均标H，完整值见simulation/config.json及parameter_sources.csv。没有把选择值假称为制造商规格。
