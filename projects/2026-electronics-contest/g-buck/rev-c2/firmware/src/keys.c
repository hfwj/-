#include "board.h"
/* Optional control-board keys PB5..PB8, active-low; NOT assigned in C.2 mainboard.
 * No key GPIO is touched in the delivered KEYS_ENABLED=0 build. */
void keys_tick(App *a){
#if KEYS_ENABLED
 static u8 initialized,stable[4],count[4];
 if(!initialized){
  REG(GPIOB+0x10)=0x1E0;
  REG(GPIOB)=(REG(GPIOB)&0x000FFFFFu)|0x88800000u;
  REG(GPIOB+4)=(REG(GPIOB+4)&~15u)|8u;
  for(u32 k=0;k<4;k++)stable[k]=1;
  initialized=1;
 }
 for(u32 k=0;k<4;k++){
  u8 bit=(REG(GPIOB+8)>>(5+k))&1;
  if(bit==stable[k]){count[k]=0;continue;}
  if(++count[k]<20)continue;
  stable[k]=bit;count[k]=0;if(bit)continue;
  if(k==0)a->edit_current^=1;
  if(k==1 || k==2){i32 delta=k==1?1:-1;
   app_command(a,a->edit_current?CMD_SET_I:CMD_SET_V,
     a->edit_current?a->iset+delta*50:a->vset+delta*100);
  }
  if(k==3){
   /* PRECHARGE/recovery via mailbox so EXTI sticky handling stays centralized. */
   extern volatile u32 debug_command;
   if(a->state==OFF || a->state==TRIPPED)debug_command=CMD_PRECHARGE;
   else if(a->state==READY)app_command(a,a->bypass_confirmed?CMD_START:CMD_CONFIRM_BYPASS,0);
   else app_command(a,CMD_STOP,0);
  }
 }
#else
 (void)a;
#endif
}
