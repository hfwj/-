from pathlib import Path
import fitz
from docx import Document
from docx.shared import Pt,Inches
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 text='''# A题最终论文初版：中文审阅说明

本版交付完整英文论文图文修订稿Draft 02、可编辑Word、PDF、Markdown源稿、9幅主文英文图（另附全程敏感性图）、9张表和原始证据索引。按官网英文论文要求组织；当前是可审阅初版，队号为TBA，完整AI记录尚待补齐，完整M1与安全着陆未证明，因此不能直接当作已完成全部要求的提交稿。

## 中文摘要

针对70 km高度、6000 km/h速率分离、干质量130 t的一级助推器海上回收，建立球形重力、分层标准大气、阻力及变质量平动模型。题目未给分离方向、发动机及姿态/支腿能力，故采用水平分离、无风、恒阻力系数0.5和比冲320 s的虚拟三发动机情景。受约束轨迹搜索得到约149 t初始液氧与甲烷总量的名义候选，参考末端前消耗约148 t。方案先滑行40 s，再三台制动，关机指令5 s后两台重启；约218 s到达206 km处的CG参考终点，峰值动压约47 kPa、参考下降速率约1 m/s。独立积分和解析检查支持名义数值结果，但保持原轨迹需至少约24.8°净推力相对箭体偏转，能力未明；9个单参数扰动均未按原开环计划通过。因此149 t仅为条件性研究候选，不是实际安全装载量或全局最低燃料。论文推导了完整姿态、脚端、包络及接触后验收框架，并明确后续数据与模型需求。

## 论文结构与阅读顺序

1. 问题解释：先回答题目给了什么、缺什么，为何真实燃料需求不唯一。
2. 假设与符号：区分题给G、参考L、假设H、未知U；虚拟发动机不冒充实机。
3. 量级与被动弹道：说明重力、曲率、大气、变质量必须保留；船位自由不能代替水平制动。
4. 主模型：极坐标平动、耗剂/残余/储备和发动机响应。
5. 轨迹求解：目标、调度策略族、名义限制、直接多重射击与独立验收。
6. 名义结果：比较少量策略，解释149.30 t携带量与147.84 t消耗量及氧燃拆分。
7. 验证与敏感性：网格、积分器、解析检查和9个固定开环扰动。
8. 姿态可行性：β、θ、δ分开；24.78°必要偏转反例及最小M1力矩框架。
9. 安全讨论：首次脚接触、脚端速度、包络、有限甲板、吸能/关机/抗倾覆和结构热。
10. 优点与局限、完善路径；第11节给条件性结论。
附录A说明计算可追溯性；附录B列18类/19条判据；文末Report on the Use of AI如实标明缺少完整历史记录。

## 九幅主图的对应位置

Figure 1（§1）为任务时序和局部几何；Figure 2（§2.1）为M0→优化→待完成M1的工作流及G/L/H/U分类；Figure 3（§3.1）为130t干机被动高度–射程三条曲线；Figure 4（§4.3）为0.5s延迟、1s限速爬升和指数尾部；Figure 5/6为原名义轨迹/控制；Figure 7（§7.2）为九扰动末段3×3对比；Figure 8为姿态必要条件；Figure 9为接触几何。表格编号不变，九扰动仍对应Table 8。

敏感性曲线重新按原模型和固定控制回放，已逐例与原汇总终点核对。曲线在实际CG参考接触、可用推进剂耗尽或计划终点停止，不外推成“成功着陆”。主图放大180s后的末段，完整0至终点轨迹另附补充图和CSV。图1角度为示意夸张姿态，不是已验证箭体轨迹；图2明确标注M1未完成。

## 对结论的必要核对

149.30 t是初始总推进剂，液氧约115.37 t、甲烷约33.93 t；147.84 t为参考终点前消耗。约711 kg可用余量与约746 kg不可用残余分别记账。

正文约1 m/s是CG高度32.5 m的代理事件，不能写成已验证脚端安全触地。自由船位只选一次；扰动不能移动船去追随落点。25°角度样本相容不是完整姿态可行，9例开环失败也不是闭环失败概率。所有安全阈值和虚拟发动机性能仍为H。

## 提交前需要完成的编辑与研究

- 填入真实队号后重建每页页眉；正文不填姓名、学校等识别信息。初稿文件名保留Draft02，真正提交前须按官网改为队号加题号，如115A.pdf。
- 主办方要求首页只有队号、题号、题名及不超过300词摘要，本版按此组织；正文英文，正文后含参考文献和文内编号。
- 官网AI规则要求记录工具、精确提问及完整输出。当前稿只准确记录本轮“写出最终论文初版”提问并说明历史缺口，尚未附历次完整对话输出。须从实际记录导出，逐字补入文末，不能伪造或用概述/仓库链接代替。
- 由团队核查全部AI文本、公式、图表、引用与数据。补齐AI记录只是格式/披露工作，不能替代M1、反馈扰动及接触后安全验证。
- 若要把论文从名义研究初稿升级为安全燃料结论，需要先明确质量特性/执行器与气动能力，重规划并通过脚端、支撑及热结构检验。

官网规则：https://university-physics-competition.com/contest-rules
题目来源：https://university-physics-competition.com/2026-competition
本版没有提交或发送任何参赛邮件。

## 复现和变更影响

simulation/prepare.py从已归档数据生成证据快照和英文图；build_paper.py生成英文Word、PDF与Markdown；build_guide.py生成本说明；validate_paper.py核对摘要、页眉、编号/占位、数学排版和数据一致性。simulation/README.md提供命令。

相对17c2b91710ad17cde9fe216096953e188eb1127a，本版新增5张科学图、九扰动同模型回放导出及正文引用/图号更新，不修改历史优化模型或输入，也未新增实际M1/闭环/接触仿真。原理图连接/管脚/器件值、器件/BOM/封装、PCB、固件及旧电子工程模型不变。
'''
 pages=len(fitz.open(ROOT/'reports/TBA_A_Draft02.pdf'))
 text=text.replace('20页',str(pages)+'页')
 (ROOT/'reports/论文初版_中文审阅说明.md').write_text(text)
 doc=Document();section=doc.sections[0];section.top_margin=section.bottom_margin=Inches(.7)
 style=doc.styles['Normal'];style.font.name='Noto Serif CJK SC';style._element.rPr.rFonts.set(qn('w:eastAsia'),'Noto Serif CJK SC');style.font.size=Pt(10)
 doc.core_properties.author='';doc.core_properties.last_modified_by=''
 for line in text.splitlines():
  if line.startswith('# '):doc.add_heading(line[2:],0)
  elif line.startswith('## '):doc.add_heading(line[3:],1)
  elif line.startswith('- '):doc.add_paragraph(line[2:],'List Bullet')
  elif line.strip():doc.add_paragraph(line)
 doc.save(ROOT/'reports/论文初版_中文审阅说明.docx')
 print('Chinese editorial guide built')
