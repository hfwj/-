"""Independently read back the saved Rev C.1 file and constrain every electrical delta."""
import csv
import json
import sqlite3
from native_common import ROOT,GBUCK,read_project,inventory,attrs,sha


def main():
    src=next((GBUCK/'rev-c/schematic/native').glob('*.eprj2'))
    dst=next((ROOT/'schematic/native').glob('*.eprj2'))
    sm,sd,_=read_project(src);dm,dd,_=read_project(dst)
    _,sp,old,op=inventory(sm,sd,'G题同步Buck Rev C 原理图')
    scheme,pages,new,np=inventory(dm,dd,'G题同步Buck Rev C.1 原理图')
    errors=[]
    def check(ok,msg):
        if not ok:errors.append(msg)
    oldnets={p['ref']+'.'+p['pin']:p['net'] for p in op}
    newnets={p['ref']+'.'+p['pin']:p['net'] for p in np}
    changes={ep:[net,newnets.get(ep)] for ep,net in oldnets.items() if newnets.get(ep)!=net}
    check(not changes,'Existing pin networks changed')
    expected={
        'R_VINP_TOP.1':'VIN','R_VINP_TOP.2':'VIN_POST_DIV',
        'R_VINP_BOT.1':'VIN_POST_DIV','R_VINP_BOT.2':'GND',
        'R_VINP_ADC.1':'VIN_POST_DIV','R_VINP_ADC.2':'ADC_VIN_POST',
        'C_VINP_ADC.1':'ADC_VIN_POST','C_VINP_ADC.2':'GND',
        'D_ADC6.1':'GND','D_ADC6.2':'+3V3_A','D_ADC6.3':'ADC_VIN_POST',
        'J_MON.1':'ADC_VIN_POST','J_MON.2':'GND','TP14.1':'ADC_VIN_POST'}
    added={ep:net for ep,net in newnets.items() if ep not in oldnets}
    check(added==expected,'New pin networks differ from the VIN monitor specification')
    check(len(new)==120 and len(pages)==9,'Unexpected component/page count')
    values={ref:[p['attrs']['Value'],new.get(ref,{}).get('attrs',{}).get('Value')]
            for ref,p in old.items() if p['attrs']['Value']!=new.get(ref,{}).get('attrs',{}).get('Value')}
    check(values=={'C_IOUT_PROT':['1nF / C0G','100nF / 25V X7R']},'Unexpected existing part value changes')
    with (ROOT/'schematic/BOM_RevC1.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    bom={r['位号']:r for r in rows}
    check(len(rows)==len(bom)==120,'BOM duplicate or missing references')
    check(set(bom)==set(new),'BOM reference inventory mismatch')
    unresolved_footprints=[]
    for ref,p in new.items():
        at=p['attrs'];device=dd[at['Device']]['META','META']['attributes']
        check(bom[ref]['数值/型号']==at['Value'],'BOM value mismatch '+ref)
        check(device['Symbol']==at['Symbol'],'Device/symbol mismatch '+ref)
        check(device['Footprint']==at['Footprint'],'Device/footprint mismatch '+ref)
        # All symbol pin numbers must exist in the chosen physical footprint.
        if not at.get('Footprint'):
            unresolved_footprints.append(ref)
            check(ref in old and old[ref]['attrs'].get('Footprint')=='',
                  'Newly unassigned footprint '+ref)
            continue
        padnums={b['num'] for (k,_),b in dd[at['Footprint']].items() if k=='PAD'}
        pinnums={p['pin'] for p in np if p['ref']==ref}
        check(pinnums<=padnums,'Footprint missing a numbered pin '+ref)
    p6=next(p for p in np if p['ref']=='J_CTL' and p['pin']=='6')
    check(p6['name']=='PB11/OC#' and p6['net']=='IOUT_OC_N','J_CTL.6 name/net mismatch')
    check(next(p for p in np if p['ref']=='J_MON' and p['pin']=='1')['name']=='PA5/ADC','J_MON.1 name incorrect')
    for ref in ('QH','QL'):
        sym=dd[new[ref]['attrs']['Symbol']]
        check(all(b.get('valueVisible') for (k,_),b in sym.items()
                  if k=='ATTR' and b.get('key') in ('Pin Name','Pin Number')),'MOS labels hidden '+ref)
    manifest=json.loads((ROOT/'results/data/build_manifest.json').read_text())
    modified=set(manifest['changed_document_ids'])
    legacy_unchanged=all(dd[u]==d for u,d in sd.items() if u not in modified)
    check(legacy_unchanged,'Unrelated design documents changed')
    check(sha(src)==manifest['source_sha256'],'Source Rev C file changed')
    con=sqlite3.connect(dst.as_uri()+'?mode=ro',uri=True)
    integrity=con.execute('pragma integrity_check').fetchone()[0];check(integrity=='ok','SQLite integrity failure')
    structure=json.loads(con.execute('SELECT structure FROM project_structures ORDER BY id DESC LIMIT 1').fetchone()[0])
    check(all(u in structure['sheets'] for u in pages),'Structural cache missing current sheets')
    check(structure['schematics'][scheme]['name']=='G题同步Buck Rev C.1 原理图','Structural cache title mismatch')
    con.close()
    out=ROOT/'results/data';out.mkdir(exist_ok=True,parents=True)
    with (out/'RevC1_逐引脚接线表.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(np[0]),lineterminator='\n');writer.writeheader();writer.writerows(np)
    result={'status':'PASS_STATIC_NATIVE_READBACK' if not errors else 'FAIL','date_beijing':'2026-10-27',
        'pages':len(pages),'parts':len(new),'nets':len({p['net'] for p in np if p['net']}),
        'connected_pins':sum(bool(p['net']) for p in np),
        'unwired_pins':[p['ref']+'.'+p['pin'] for p in np if not p['net']],
        'existing_network_changes':changes,'existing_value_changes':values,
        'new_pin_specification':expected,'new_refs':sorted(set(new)-set(old)),
        'j_ctl_6':p6,'source_unchanged':sha(src)==manifest['source_sha256'],
        'unrelated_design_documents_unchanged':legacy_unchanged,'sqlite_integrity':integrity,
        'unassigned_footprints_inherited_from_RevC':unresolved_footprints,
        'nominal_monitor':{'ratio':11,'adc_at_25V_V':25/11,
            'divider_power_at_25V_W':25**2/110000,
            'filter_tau_s':(1/(1/100000+1/10000)+1000)*4.7e-9},
        'iout_alert_RC_s':1000*100e-9,'native_sha256':sha(dst),
        'native_client_open_test':False,'native_erc_run':False,'pcb_drc_run':False,
        'dynamic_simulation_run':False,'actual_firmware_test':False,'hardware_measurements':False,
        'errors':errors}
    (out/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
