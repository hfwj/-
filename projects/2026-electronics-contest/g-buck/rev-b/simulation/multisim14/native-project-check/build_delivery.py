"""Check evidence and package the native project revision for local review."""
import hashlib,json,re,struct,zipfile
from pathlib import Path
import dclimplode
from ms14_project import ROOT,PROJECT,SOURCE,DEST,PRECHARGE,MAGIC,unpack,parse,inspect


def main():
    data=ROOT/'results/data'
    info=json.loads((data/'project_inspection.json').read_text())
    checks=json.loads((data/'driver_verification.json').read_text())
    attempts=json.loads((data/'power_stage_attempts.json').read_text())['results']
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert info['source_sha256']==checks['source_project_sha256']==digest(SOURCE)
    assert info['corrected_sha256']==checks['corrected_project_sha256']==digest(DEST)
    assert info['pre_pwm_check_sha256']==digest(PRECHARGE)
    assert len(checks['results'])==3 and all(r['completed'] for r in checks['results'])
    assert all(r['end_time_s']>=.0001*.999 for r in checks['results'])
    assert checks['native_multisim_execution_verified'] is False
    by={r['case']:r for r in attempts}
    assert by['corrected_pre_pwm_check']['full_transient_completed']
    assert by['corrected_pre_pwm_check']['requested_end_time_s']==.001
    # Early-aborted full cases remain explicit; native solver outcome is unknown.
    assert not by['original_power_stage']['full_transient_completed']
    assert not by['corrected_power_stage']['full_transient_completed']
    files=[SOURCE,DEST,PRECHARGE]
    for path in files:
        packed=path.read_bytes();plain,_=unpack(packed);pos=len(MAGIC)+8;other=[]
        while pos<len(packed):
            n,c=struct.unpack_from('<II',packed,pos)
            dec=dclimplode.decompressobj_pklib();part=dec.decompress(packed[pos+8:pos+8+c])
            for _ in range(10):
                if dec.eof:break
                more=dec.decompress(b'');part+=more
                assert more or dec.eof
            assert dec.eof
            assert len(part)==n;other.append(part);pos+=8+c
        assert b''.join(other)==plain,'Independent DCL decoders disagree'
    original=unpack(SOURCE.read_bytes())[0].decode('ascii')
    revised=unpack(DEST.read_bytes())[0].decode('ascii')
    restored=revised
    for p in info['changes']:
        pattern=rf'({p["model_element"]}[^\n]*?){re.escape(p["after"])}'
        restored,n=re.subn(pattern,rf'\g<1>{p["before"]}',restored);assert n==2
    pattern=r'(<CiModel Class="CiModel" LocalName="&amp;ASCIR2104/IR__MOSFET_DRIVER__1" ChangedByUser=")1(")'
    restored,n=re.subn(pattern,r'\g<1>0\2',restored);assert n==1
    assert restored==original,'Unexpected changes outside the model patch'
    assert inspect(parse(original.encode()))==inspect(parse(revised.encode()))
    release={'date':'2026-10-24','original_and_two_native_copies_decoded_by_two_independent_implementations':True,
             'only_eight_internal_model_values_and_one_model_modified_flag_changed_in_5ms_copy':True,
             'all_three_isolated_driver_tests_completed':True,'one_ms_pre_pwm_cross_solver_check_completed':True,
             'five_ms_power_stage_cross_solver_completed':False,'native_multisim_open_or_run_verified':False,
             'files':[{ 'path':str(p.relative_to(PROJECT)),'sha256':digest(p),'bytes':p.stat().st_size} for p in files]}
    (data/'delivery_checks.json').write_text(json.dumps(release,ensure_ascii=False,indent=2)+'\n')
    orig=by['original_power_stage'];new=by['corrected_power_stage'];pre=by['corrected_pre_pwm_check']
    report=f'''# 用户Multisim工程空白波形排查

日期：2026-10-24。来源：用户上传的设计1.ms14，SHA256 `{digest(SOURCE)}`。

工程内的主要端点连接、0/3.3V测试源、2ms延时、1μs脉宽、10μs周期及0～5ms/50ns瞬态设置已核对。发现一处模型兼容性问题：内嵌IR2104输入网络的上升门限约4.986V，独立交叉求解中无法接受3.3V高电平。整机原模型交叉尝试的输出约0.964mV，与此前图上毫伏级坐标范围相符；这解释了未驱动现象，但不单凭此认定所有图表显示问题已解决。

输入比较网络的四个内部电阻由3.45Meg/46.55Meg改为5.62Meg/18.3Meg，适配本工程0/3.3V输入；独立测试的上升/下降门限约2.892V/0.798V。同步修改原文件中的两份保存模型，并标记为用户修改模型。5ms副本其余XML字节、主电路、信号源和设置不变；1ms副本另外只调整活动瞬态分析终止时间。这是兼容性修订，不是厂家认证模型或实测门限。

## 本机检查文件

- [1ms驱动使能检查](../downloads/{PRECHARGE.name})：PWM仍延时2ms，先检查低侧驱动使能。
- [5ms模型修订工程，待本机验证](../downloads/{DEST.name})：用于继续检查PWM启动。
- [完整步骤、修改范围和复现说明](../simulation/multisim14/native-project-check/README.md)。

这些是对用户原生压缩XML工程的最小修改副本，已核对容器长度、两种DCL解压实现和反向还原原XML；当前环境未启动Multisim，尚未验证本机打开或运行。建议先下载1ms检查文件，在Multisim用“文件→打开”后点击Run；若G_L获得约12V，再继续5ms文件。

## 证据与限制

| 检查 | 实际结果 |
|---|---|
| 独立原模型、3.3V | 完整100μs；HO/LO最大约2.74μV，未驱动 |
| 独立原模型、6V诊断 | 完整100μs；HO/LO最大约11.99V，能切换 |
| 独立修订模型、3.3V | 完整100μs；HO/LO最大约11.99V，能切换 |
| 修订模型1ms预PWM功率级 | 完成至{pre['end_time_s']*1000:.3f}ms；G_L约{pre['pre_pwm_GL_range_V'][0]:.3f}V |
| 原模型5ms功率级尝试 | 仅至{orig['end_time_s']*1000:.6f}ms；Q2内部VFI2步长过小，未完成 |
| 修订模型5ms功率级尝试 | 仅至{new['end_time_s']*1000:.6f}ms；Q1内部VFI2步长过小，未完成 |

上述全部求解均由ngspice 44.2的PSpice兼容模式执行。独立驱动用固定12V的VB/VCC、VS=0和1nF/100kΩ输出负载，不能代表完整Buck。完整功率级交叉尝试只将F1替代为其导通电阻1mΩ，不执行Multisim保险丝交互脚本。ngspice解析时另做子电路名及参数语法适配，未把这些变换写入原生工程。

日志、原始采样、模型哈希和完成状态见[核验目录](../simulation/multisim14/native-project-check/results/)。未将任何早退结果计为5ms通过，也不能认定Multisim一定出现或已经消除同样的数值问题。当前用户工程为开环功率级与驱动测试，不构成G题闭环、保护、效率或实物验证。
'''
    (PROJECT/'reports/Multisim14_用户工程空白波形排查_2026-10-24.md').write_text(report)
    archive=PROJECT/'downloads/Multisim14_用户工程排查与修订副本_2026-10-24.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(ROOT.rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:z.write(path,path.relative_to(PROJECT))
        for path in files:z.write(path,path.relative_to(PROJECT))
        report_path=PROJECT/'reports/Multisim14_用户工程空白波形排查_2026-10-24.md'
        z.write(report_path,report_path.relative_to(PROJECT))
        z.writestr('请先阅读.txt','先打开downloads目录内的1ms检查工程，再测试5ms模型修订工程。详细说明位于simulation/multisim14/native-project-check/README.md。原件位于references/user-projects。当前环境未完成Multisim本机打开或运行；5ms交叉求解有步长失败，详见报告。')
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    print(json.dumps(release,ensure_ascii=False,indent=2));print(archive)


if __name__=='__main__':main()
