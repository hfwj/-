"""Analyze same-row native U4 boundaries; retain original adaptive samples."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from build_diagnostics import ROOT


def main(path):
    a=np.load(path);t=a['time'];ip=a['V(l_raw)'];im=a['V(v_cap)']
    cm=(ip+im)/2;diff=ip-im;vs=a['V(vdda)'];out=a['V(il_bi)']
    hg=a['V(g_h)']-a['V(sw)'];tail=t>=t[-1]-100e-6
    vectors={'L_RAW_V':ip,'V_CAP_V':im,'common_mode_V':cm,'differential_V':diff,
        'IL_BI_V':out,'VDDA_V':vs,'IL_A':a['I(L1)'],'IOUT_A':a['I(RS_OUT)'],
        'VOUT_V':a['V(vout)'],'IOUT_RAW_V':a['V(iout_raw)'],
        'high_VGS_V':hg,'low_VGS_V':a['V(g_l)'],'SW_V':a['V(sw)']}
    metrics={k:{'min':float(v[tail].min()),'max':float(v[tail].max()),'last':float(v[-1])} for k,v in vectors.items()}
    cross=np.flatnonzero((cm[:-1]-5)*(cm[1:]-5)<0)
    result={'date':'2026-10-25','source':'native GRA from all four original RAR volumes',
        'samples_per_trace':len(t),'end_s':float(t[-1]),'tail_start_s':float(t[tail][0]),
        'tail_points':int(tail.sum()),'tail_100us':metrics,
        'terminal_common_mode_minus_5V_V':float(cm[-1]-5),
        'strict_sign_crossing_brackets':int(len(cross)),
        'last_10_crossing_brackets_s':[[float(t[i]),float(t[i+1])] for i in cross[-10:]],
        'near_terminal_equal_5V_points':int(np.sum((t>=t[-1]-1e-6)&(cm==5))),
        'min_recorded_time_increment_s':float(np.diff(t).min()),
        'VDDA_tail_peak_to_peak_V':float(np.ptp(vs[tail])),
        'observation':'terminal U4 common mode exactly matches embedded IIBP/IIBN 5V breakpoint in decoded binary64; power-stage current and supply do not show a gross runaway/collapse in this recorded window',
        'limitation':'Correlation is not sole-cause proof. Last accepted points omit failed Newton trials; no F1 status, actual hardware shoot-through or full 25ms success is inferred.'}
    (ROOT/'results/data/native_u4_boundary_analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    selected=t>=t[-1]-30e-6
    np.savetxt(ROOT/'results/data/native_u4_last_30us.csv',np.column_stack([
        t[selected],*[v[selected] for v in vectors.values()]]),delimiter=',',
        header=','.join(['time_s',*vectors]),comments='',fmt='%.17e')
    fig,axs=plt.subplots(4,1,figsize=(11,9),sharex=True)
    xx=(t[tail]-t[-1])*1e6
    axs[0].plot(xx,(cm[tail]-5)*1e3,lw=1);axs[0].axhline(0,color='r',ls='--',label='model IIB breakpoint')
    axs[0].set_ylabel('VCM - 5 V / mV');axs[0].legend()
    axs[1].plot(xx,diff[tail]*1e3);axs[1].set_ylabel('IN+ - IN- / mV')
    axs[2].plot(xx,out[tail],label='native IL_BI');axs[2].plot(xx,(vs/2+20*diff)[tail],label='static expression only',alpha=.7)
    axs[2].set_ylabel('Output / V');axs[2].legend()
    axs[3].plot(xx,(vs[tail]-vs[-1])*1e9);axs[3].set_ylabel('VDDA - final / nV');axs[3].set_xlabel('Time relative to last accepted point / us')
    for ax in axs:ax.grid(alpha=.25)
    fig.suptitle('Native U4 boundary: end 16.440824408 ms, not a completed 25 ms run')
    fig.tight_layout();fig.savefig(ROOT/'results/figures/native_u4_boundary_last100us.png',dpi=150);plt.close(fig)
    # Last 1 us; real adaptive points, no resampling or claimed failed-step data.
    narrow=t>=t[-1]-1e-6;xx=(t[narrow]-t[-1])*1e9
    fig,axs=plt.subplots(3,1,figsize=(11,7),sharex=True)
    axs[0].plot(xx,(cm[narrow]-5)*1e6,'.-',ms=2);axs[0].axhline(0,color='r',ls='--');axs[0].set_ylabel('VCM - 5 V / uV')
    axs[1].plot(xx,hg[narrow],label='GH-SW');axs[1].plot(xx,a['V(g_l)'][narrow],label='GL');axs[1].set_ylabel('External VGS / V');axs[1].legend()
    axs[2].plot(xx,a['I(L1)'][narrow]);axs[2].set_ylabel('IL / A');axs[2].set_xlabel('Time relative to last accepted point / ns')
    for ax in axs:ax.grid(alpha=.25)
    fig.tight_layout();fig.savefig(ROOT/'results/figures/native_u4_terminal_edge.png',dpi=150);plt.close(fig)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('cache',type=Path);args=parser.parse_args();main(args.cache)
