#include "app.h"
static i32 clamp(i32 x,i32 lo,i32 hi){return x<lo?lo:(x>hi?hi:x);}
void app_init(App *a){
 *a=(App){0}; a->vset=10000; a->iset=1000; a->state=OFF;
}
void app_trip(App *a,Fault f){
 a->enable=0; a->arm=0; a->duty=0; a->fault=f; a->state=TRIPPED;
 a->bypass_confirmed=0; a->age=a->oc_ms=a->uv_ms=a->pre_ms=0;
}
void app_command(App *a,Command c,i32 v){
 if(c==CMD_STOP){i32 vs=a->vset,is=a->iset;app_init(a);a->vset=vs;a->iset=is;return;}
 /* Settings may only change with the stage stopped; do not restart implicitly. */
 if(c==CMD_SET_V && (a->state==OFF || a->state==TRIPPED)) a->vset=clamp(v,200,10000);
 if(c==CMD_SET_I && (a->state==OFF || a->state==TRIPPED)) a->iset=clamp(v,100,1000);
 if(c==CMD_PRECHARGE && (a->state==OFF || a->state==TRIPPED)){
  a->state=PRECHARGE;a->fault=F_NONE;a->pre_ms=0;a->bypass_confirmed=0;
 }
 if(c==CMD_CONFIRM_BYPASS && a->state==READY) a->bypass_confirmed=1;
 if(c==CMD_START && a->state==READY && a->bypass_confirmed && POWER_STAGE_ALLOWED){
  a->state=ARMING;a->age=0;a->cv=a->cc=a->cv_rem=a->cc_rem=a->ev_old=a->ei_old=0;
  a->oc_ms=a->uv_ms=0;
 }
}
static i32 pi(i32 out,i32 e,i32 old,i32 kp,i32 ki,i32 *rem){
 i32 numerator=kp*(e-old)+ki*e+*rem;
 i32 next=out+numerator/1000;
 *rem=numerator%1000;
 if(next<0 || next>DUTY_MAX)*rem=0;
 return clamp(next,0,DUTY_MAX);
}
void app_tick(App *a,const Sample *s,u8 fault_n,u8 oc_n){
 a->arm=0;
 if(!fault_n){app_trip(a,F_HARDWARE);return;}
 if(a->state==OFF || a->state==TRIPPED)return;
 if(!s->valid){app_trip(a,F_ADC);return;}
 if(s->vin<VIN_MIN_MV || s->vin>VIN_MAX_MV){app_trip(a,F_INPUT);return;}
 /* Also observe precharge voltage throughout operation, not just before ARM. */
 if(s->vin_post<11000 && a->state>=ARMING){app_trip(a,F_INPUT);return;}
 if(a->state==PRECHARGE){
  if(s->vin_post>=s->vin-1500 && s->vin_post>=11000){
   if(++a->pre_ms>=PRECHARGE_MS)a->state=READY;
  }else a->pre_ms=0;
  return;
 }
 if(a->state==READY){
  if(s->vin_post<s->vin-1500){a->state=PRECHARGE;a->pre_ms=0;a->bypass_confirmed=0;}
  return;
 }
 if(s->vout>11500){app_trip(a,F_OV);return;}
 if(a->state==ARMING){
  if(!oc_n){app_trip(a,F_OC);return;}
  /* 1ms positive ARM pulse, then settle 1ms, still disabled. */
  if(a->age==0)a->arm=1;
  if(++a->age>=2){a->state=SOFTSTART;a->age=0;a->enable=1;}
  return;
 }
 if(s->vout>11500){app_trip(a,F_OV);return;}
 if(!oc_n){if(++a->oc_ms>=OC_DELAY_MS){app_trip(a,F_OC);return;}}else a->oc_ms=0;
 if(a->state==RUN && a->vset>1000 && s->vout<500){
  if(++a->uv_ms>=UV_DELAY_MS){app_trip(a,F_LOW_OUTPUT);return;}
 }else a->uv_ms=0;
 i32 target=a->vset;
 if(a->state==SOFTSTART){
  if(++a->age>=SOFTSTART_MS){a->state=RUN;}else target=(i32)(a->age*(u32)a->vset/SOFTSTART_MS);
 }
 i32 ev=target-s->vout,ei=a->iset-s->iout;
 a->cv=pi(a->cv,ev,a->ev_old,CV_KP,CV_KI,&a->cv_rem);
 a->cc=pi(a->cc,ei,a->ei_old,CC_KP,CC_KI,&a->cc_rem);
 a->ev_old=ev;a->ei_old=ei;
 a->cc_mode=a->cc<a->cv;
 a->duty=a->cc_mode?a->cc:a->cv;
 /* Track non-selected regulator to limit mode-switch windup. */
 if(a->cv>a->duty+300){a->cv=a->duty+300;a->cv_rem=0;}
 if(a->cc>a->duty+300){a->cc=a->duty+300;a->cc_rem=0;}
}
