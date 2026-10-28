#include <assert.h>
#include <stdio.h>
#include "app.h"
static Sample healthy={25000,400,10000,500,500,24500,1};
static void step(App *a,Sample s,int n,u8 oc){while(n--)app_tick(a,&s,1,oc);}
static void ready(App *a){app_init(a);app_command(a,CMD_PRECHARGE,0);step(a,healthy,99,1);assert(a->state==PRECHARGE);step(a,healthy,1,1);assert(a->state==READY);}
static void running(App *a){ready(a);app_command(a,CMD_CONFIRM_BYPASS,0);app_command(a,CMD_START,0);step(a,healthy,1,1);assert(a->arm && !a->enable);step(a,healthy,1,1);assert(!a->arm && a->enable);step(a,healthy,300,1);assert(a->state==RUN);}
int main(void){App a;Sample s;u16 raw[6]={2820,620,1128,1241,2048,2764};
 app_init(&a);assert(!a.enable && a.state==OFF && a.vset==10000 && a.iset==1000);
 ready(&a);app_command(&a,CMD_START,0);assert(a.state==READY); /* no bypass confirmation */
 running(&a);step(&a,healthy,4,0);step(&a,healthy,10,1);step(&a,healthy,3,0);assert(a.state==RUN);
 running(&a);step(&a,healthy,19,0);assert(a.state==RUN);step(&a,healthy,1,0);assert(a.state==TRIPPED && a.fault==F_OC && !a.enable && !a.duty);
 step(&a,healthy,1000,1);assert(a.state==TRIPPED);app_command(&a,CMD_START,0);assert(a.state==TRIPPED);
 app_command(&a,CMD_PRECHARGE,0);step(&a,healthy,100,1);assert(a.state==READY && !a.bypass_confirmed);
 running(&a);s=healthy;s.vout=100;step(&a,s,19,1);assert(a.state==RUN);step(&a,s,1,1);assert(a.fault==F_LOW_OUTPUT);
 running(&a);s=healthy;s.vout=10;step(&a,s,20,1);assert(a.fault==F_LOW_OUTPUT); /* independent of OC */
 running(&a);s=healthy;s.vout=100;step(&a,s,19,1);step(&a,healthy,1,1);step(&a,s,19,1);assert(a.state==RUN);
 ready(&a);app_command(&a,CMD_CONFIRM_BYPASS,0);app_command(&a,CMD_START,0);step(&a,healthy,2,1);s=healthy;s.vout=0;step(&a,s,299,1);assert(a.state==SOFTSTART);step(&a,s,1,1);assert(a.state==RUN);step(&a,s,20,1);assert(a.fault==F_LOW_OUTPUT);
 ready(&a);app_command(&a,CMD_STOP,0);app_command(&a,CMD_SET_V,200);app_command(&a,CMD_PRECHARGE,0);step(&a,healthy,100,1);app_command(&a,CMD_CONFIRM_BYPASS,0);app_command(&a,CMD_START,0);step(&a,healthy,302,1);s=healthy;s.vout=100;step(&a,s,100,1);assert(a.state==RUN);
 running(&a);app_tick(&a,&healthy,0,1);assert(a.fault==F_HARDWARE && !a.enable);step(&a,healthy,100,1);assert(a.state==TRIPPED);
 running(&a);s=healthy;s.valid=0;step(&a,s,1,1);assert(a.fault==F_ADC);
 running(&a);s=healthy;s.vin=11000;step(&a,s,1,1);assert(a.fault==F_INPUT);
 running(&a);s=healthy;s.vin=28000;step(&a,s,1,1);assert(a.fault==F_INPUT);
 running(&a);s=healthy;s.vin_post=10000;step(&a,s,1,1);assert(a.fault==F_INPUT);
 running(&a);s=healthy;s.vout=12000;step(&a,s,1,1);assert(a.fault==F_OV);
 ready(&a);s=healthy;s.vin_post=22000;step(&a,s,1,1);assert(a.state==PRECHARGE && !a.bypass_confirmed);
 running(&a);app_command(&a,CMD_SET_V,2000);assert(a.vset==10000);app_command(&a,CMD_STOP,0);assert(!a.enable && !a.duty);
 app_command(&a,CMD_SET_V,99999);app_command(&a,CMD_SET_I,-1);assert(a.vset==10000 && a.iset==100);
 adc_convert(raw,&s);assert(s.valid && s.vin>24900 && s.vin<25100 && s.vout>9900 && s.vout<10100 && s.iout>990 && s.iout<1010 && s.il>=-2 && s.il<=2);
 raw[4]=1427;adc_convert(raw,&s);assert(s.il<-990 && s.il>-1010);raw[4]=2668;adc_convert(raw,&s);assert(s.il>990 && s.il<1010);
 raw[0]=4095;adc_convert(raw,&s);assert(!s.valid);raw[0]=2820;raw[4]=0;adc_convert(raw,&s);assert(!s.valid);
 running(&a);for(int n=0;n<10000;n++){s=healthy;s.vout=2000+n%9000;s.iout=500+n%1000;step(&a,s,1,1);assert(a.duty>=0 && a.duty<=DUTY_MAX);assert(a.duty==(a.cc<a.cv?a.cc:a.cv));}
 running(&a);a.cv=1000;a.cc=1300;a.ev_old=1;a.ei_old=100;
 s=healthy;s.vout=9999;s.iout=900;step(&a,s,500,1);assert(a.cv>1000); /* fractional integrator survives a 1mV error */
 puts("PASS: state transitions, ARM pulse, bypass interlock, timed OC/UV, low-target/startup exemptions, manual recovery, ADC scaling/rails, input/OV faults, setpoint limits and duty bounds");
}
