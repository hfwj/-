"""Check model passive nets/values against previously PDF-extracted pin/value tables."""
from pathlib import Path
import csv,json,re,hashlib,itertools
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[3]
DRAW=ROOT.parents[1]/'original-schematic'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def spice_value(s):
    m=re.fullmatch(r'([0-9.]+)([kmunp]?)',s,re.I);assert m,s
    return float(m[1])*{'':1,'k':1e3,'m':1e-3,'u':1e-6,'n':1e-9,'p':1e-12}[m[2].lower()]
def original_value(s):
    m=re.match(r'([0-9.]+)([kmunpμ]?)(?:Ω|F)',s);assert m,s
    return float(m[1])*{'':1,'k':1e3,'m':1e-3,'u':1e-6,'μ':1e-6,'n':1e-9,'p':1e-12}[m[2]]
def main():
    with (DRAW/'逐引脚接线表.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
    pins={r['reference']+'.'+r['physical_pin']:r['network'] for r in rows}
    with (DRAW/'原图元件与Multisim选择.csv').open(encoding='utf-8-sig') as f:values={r['reference']:r['original_value'] for r in csv.DictReader(f)}
    alias={'VDIG':'+3V3','VA':'+3V3_A','V5':'+5V','COM':'GND'};checks=[];assumptions=[]
    for line in (ROOT/'REVB_SENSE_PROTECT.lib').read_text().splitlines():
        bits=line.split()
        if not bits or bits[0][0] not in 'RC':continue
        ref=bits[0]
        if ref not in values:assumptions.append(ref);continue
        assert len(bits)>=4
        nets=[alias.get(x,x) for x in bits[1:3]]
        assert nets==[pins[ref+'.1'],pins[ref+'.2']],(ref,nets)
        actual=spice_value(bits[3]);expected=original_value(values[ref]);assert abs(actual-expected)<abs(expected)*1e-10
        checks.append({'reference':ref,'nets':nets,'model_value':bits[3],'PDF_table_value':values[ref],'matched':True})
    active_pins={'U2.1':'VIN','U2.8':'V_SHUNT_IN','U2.7':'GND','U2.3':'GND','U2.6':'+3V3_A','U2.5':'IIN_RAW','U3.3':'V_CAP','U3.4':'VOUT','U3.5':'GND','U3.6':'+3V3_A','U3.1':'IOUT_RAW','U4.8':'L_RAW','U4.1':'V_CAP','U4.7':'+3V3_A','U4.3':'GND','U4.5':'IL_BI','U5.3':'VREF_POS','U5.2':'IL_BI','U5.1':'FAULT_N','U5.5':'VREF_OV','U5.6':'VOUT_DIV','U5.7':'FAULT_N','U5.8':'+5V','U9.3':'IL_BI','U9.2':'VREF_NEG','U9.1':'FAULT_N','U9.8':'+5V','U6.1':'FAULT_N','U6.2':'+3V3','U6.3':'ARM','U6.4':'+3V3','U6.5':'SAFE_OK','U7.1':'SAFE_OK','U7.2':'MCU_EN','U7.3':'DRV_EN','U8.1':'POR_RC','U8.2':'POR_INV','U8.3':'POR_INV','U8.4':'POR_OK','D_POR.1':'FAULT_N','D_POR.3':'POR_OK'}
    for p,net in active_pins.items():assert pins[p]==net,(p,pins[p],net)
    for n,net in enumerate(['ADC_VIN','ADC_IIN','ADC_VOUT','ADC_IOUT','ADC_IL'],1):
        assert [pins[f'D_ADC{n}.{k}'] for k in [1,2,3]]==['GND','+3V3',net]
    filter_tau={'ADC_VIN_s':(1000+100000*10000/(100000+10000))*4.7e-9,'ADC_VOUT_s':(1000+10000*1000/(10000+1000))*4.7e-9,'ADC_current_external_RC_s':1000*4.7e-9,'reference_POS_NEG_s':(10000*34000/44000)*100e-9,'reference_OV_s':(23000*10000/33000)*100e-9,'POR_R14_C11_s':10000*100e-9}
    pos=[];neg=[];ov=[]
    for va in [3.135,3.3,3.465]:
        for r9,r10a,r10b in itertools.product([10000*.999,10000*1.001],[33000*.999,33000*1.001],[1000*.999,1000*1.001]):pos.append(2*va*((r10a+r10b)/(r9+r10a+r10b)-.5))
        for r15a,r15b,r16 in itertools.product([33000*.999,33000*1.001],[1000*.999,1000*1.001],[10000*.999,10000*1.001]):neg.append(2*va*(r16/(r15a+r15b+r16)-.5))
        for r11,r12,r4,r5 in itertools.product([23000*.99,23000*1.01],[10000*.99,10000*1.01],[10000*.999,10000*1.001],[1000*.999,1000*1.001]):ov.append(va*r12/(r11+r12)*(r4+r5)/r5)
    report={'date':'2026-10-24','schematic_pdf_sha256':sha(PROJECT/'references/G题同步Buck完整原理图_RevB.pdf'),'BOM_docx_sha256':sha(PROJECT/'references/G题同步Buck完整物料清单_RevB_变化标注版.docx'),'pin_table_sha256':sha(DRAW/'逐引脚接线表.csv'),'physical_passive_checks':checks,'physical_passives_matched':len(checks),'active_used_pin_polarities_matched':len(active_pins),'BAT54S_midpoint_orientations_matched':5,'model_only_RC_elements_not_new_BOM_parts':assumptions,'nominal_at_exact_3p3V_A':{'IL_zero_V':1.65,'VREF_POS_V':2.55,'VREF_NEG_V':.75,'VREF_OV_V':1,'IL_trip_A':[-1.8,1.8],'VOUT_OV_V':11},'passive_time_constants':filter_tau,'analytical_tolerance_scenarios':{'assumed_analog_supply_V':[3.135,3.465],'supply_range_is_study_assumption_not_regulator_spec':True,'current_ref_resistor_tolerance':.001,'OV_ref_R11_R12_tolerance':.01,'output_divider_tolerance':.001,'positive_IL_threshold_range_A':[min(pos),max(pos)],'negative_IL_threshold_range_A':[min(neg),max(neg)],'VOUT_OV_threshold_range_V':[min(ov),max(ov)],'scope':'Resistor/supply corners only, not amplifier/comparator offsets, actual rail consumption or certified worst-case timing'},'F1_review':{'location':'Input VIN_EXT->FUSED beforeD1','nominal_rating_A':2,'sense_domain':'Input current, not output current or direct inductor-current clamp','melting_time_verified':False,'reason':'BOM specifies2A/5x20 but no manufacturer time-current/I2t curve; cross-solver substitutes1mOhm. Native rated-fuse behavior is not a physical fuse qualification.'}}
    (ROOT/'results/data/source_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    selected={r['reference'] for r in rows if r['reference'] in {x['reference'] for x in checks} or r['reference'] in ['U2','U3','U4','U5','U6','U7','U8','U9','D_POR'] or r['reference'].startswith('D_ADC')}
    with (ROOT/'results/data/original_protection_pin_map.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(r for r in rows if r['reference'] in selected)
    print(json.dumps({'physical_passives_matched':len(checks),'active_pins_matched':len(active_pins),'time_constants':filter_tau,'tolerance':report['analytical_tolerance_scenarios']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
