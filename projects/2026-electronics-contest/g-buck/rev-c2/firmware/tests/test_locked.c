#include <assert.h>
#include <stdio.h>
#include "app.h"
int main(void){App a;Sample s={25000,0,0,0,0,24500,1};app_init(&a);
 app_command(&a,CMD_PRECHARGE,0);for(int i=0;i<100;i++)app_tick(&a,&s,1,1);
 app_command(&a,CMD_CONFIRM_BYPASS,0);app_command(&a,CMD_START,0);
 for(int i=0;i<1000;i++){app_tick(&a,&s,1,1);assert(!a.enable && !a.arm && !a.duty && a.state==READY);}
 puts("PASS: delivered POWER_STAGE_ALLOWED=0 image never ARM/enables PWM");}
