"""Same-row native boundary analysis for the 24.9514ms Q2 failure."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from build_diagnostics import ROOT


def main(cache):
    z=np.load(cache);t=z['time'];sw=z['V(sw)'];hi=z['V(g_h)']-sw;lo=z['V(g_l)']
    cm=(z['V(l_raw)']+z['V(v_cap)'])/2;di=z['V(l_raw)']-z['V(v_cap)']
    u3cm=(z['V(v_cap)']+z['V(vout)'])/2
    assert len(t)==815260 and abs(t[-1]-.0249514)<5e-8
    tail=t>=t[-1]-100e-6
    vectors={'high_VGS_V':hi,'low_VGS_V':lo,'SW_V':sw,'IL_A':z['I(L1)'],
        'VDDA_V':z['V(vdda)'],'VOUT_V':z['V(vout)'],'IOUT_A':z['I(RS_OUT)'],
        'IOUT_RAW_V':z['V(iout_raw)'],'IL_BI_V':z['V(il_bi)'],
        'U4_common_mode_V':cm,'U4_differential_V':di,'U3_common_mode_V':u3cm}
    stats={k:{'min':float(v[tail].min()),'max':float(v[tail].max()),'last':float(v[-1])} for k,v in vectors.items()}
    edges=np.flatnonzero((sw[:-1]<12)&(sw[1:]>=12));events=[]
    for i in edges[-4:]:
        ix=np.flatnonzero((t>=t[i]-.1e-6)&(t<=t[i]+.5e-6));p=ix[np.argmax(lo[ix])]
        events.append({'SW_12V_crossing_left_bracket_s':float(t[i]),'low_gate_peak_time_s':float(t[p]),
            'low_VGS_peak_V':float(lo[p]),'high_VGS_same_row_V':float(hi[p]),'IL_same_row_A':float(z['I(L1)'][p])})
    result={'date':'2026-10-26','source':'native GRA from six original RAR volumes',
        'points_per_trace':len(t),'last_time_s':float(t[-1]),'requested_end_s':.1,
        'native_100ms_completed':False,'tail_start_s':float(t[tail][0]),'tail_points':int(tail.sum()),
        'tail_100us':stats,'last_four_SW_rise_low_gate_peaks':events,
        'min_recorded_time_increment_s':float(np.diff(t).min()),
        'F1_status':'user explicitly confirmed not blown with corresponding log',
        'observation':'Final accepted point has Q2 external VGS near zero, high-side VGS about 10.2V, stable VDDA and IL about .954A. U4 common mode is above 5V. Corrected analysis adds previously omitted U3 common mode, which is about 5V at this same native stop point.',
        'limitations':'No failed Newton iterations or native Q2 drain current. IL and F1 alone cannot exclude brief bridge cross-conduction. Last gate peaks are model/native numeric data, not hardware measurements.'}
    (ROOT/'results/data/2026-10-26_native_q2_boundary_analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    np.savetxt(ROOT/'results/data/2026-10-26_native_q2_last100us.csv',
        np.column_stack([t[tail],*[a[tail] for a in vectors.values()]]),delimiter=',',
        header=','.join(['time_s',*vectors]),comments='',fmt='%.17e')
    fig,axs=plt.subplots(4,1,figsize=(11,9),sharex=True);xx=(t[tail]-t[-1])*1e6
    axs[0].plot(xx,hi[tail],label='GH-SW');axs[0].plot(xx,lo[tail],label='GL');axs[0].set_ylabel('External VGS / V');axs[0].legend()
    axs[1].plot(xx,sw[tail]);axs[1].set_ylabel('SW / V')
    axs[2].plot(xx,z['I(L1)'][tail],label='IL');axs[2].plot(xx,z['I(RS_OUT)'][tail],label='IOUT');axs[2].set_ylabel('Current / A');axs[2].legend()
    axs[3].plot(xx,cm[tail],label='U4 common mode');axs[3].plot(xx,z['V(vout)'][tail],label='VOUT');axs[3].plot(xx,u3cm[tail],label='U3 common mode');axs[3].axhline(5,color='gray',ls='--',lw=.8);axs[3].set_ylabel('Voltage / V');axs[3].legend();axs[3].set_xlabel('Time relative to final accepted point / us')
    for ax in axs:ax.grid(alpha=.25)
    fig.suptitle('Native Q2 failure: end 24.951441601 ms; requested 100 ms not completed');fig.tight_layout()
    fig.savefig(ROOT/'results/figures/2026-10-26_native_q2_last100us.png',dpi=150);plt.close(fig)
    m=t>=t[-1]-2e-6;xx=(t[m]-t[-1])*1e9
    fig,axs=plt.subplots(3,1,figsize=(11,7),sharex=True)
    axs[0].plot(xx,hi[m],'.-',ms=2,label='GH-SW');axs[0].plot(xx,lo[m],'.-',ms=2,label='GL');axs[0].set_ylabel('External VGS / V');axs[0].legend()
    axs[1].plot(xx,sw[m],'.-',ms=2);axs[1].set_ylabel('SW / V')
    axs[2].plot(xx,z['I(L1)'][m],'.-',ms=2);axs[2].set_ylabel('IL / A');axs[2].set_xlabel('Time relative to final accepted point / ns')
    for ax in axs:ax.grid(alpha=.25)
    fig.tight_layout();fig.savefig(ROOT/'results/figures/2026-10-26_native_q2_terminal_edge.png',dpi=150);plt.close(fig)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('cache',type=Path);args=p.parse_args();main(args.cache)
