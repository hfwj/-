#include "board.h"
extern u32 _estack,_sidata,_sdata,_edata,_sbss,_ebss;
extern int main(void);
extern void SysTick_Handler(void),EXTI15_10_IRQHandler(void);
void Default_Handler(void){board_kill();while(1){}}
void Reset_Handler(void){
 u32 *source=&_sidata;
 for(u32 *p=&_sdata;p<&_edata;)*p++=*source++;
 for(u32 *p=&_sbss;p<&_ebss;)*p++=0;
 main();Default_Handler();
}
__attribute__((section(".isr_vector"),used))
void (* const vectors[76])(void)={
 [0]=(void (*)(void))(&_estack),[1]=Reset_Handler,
 [2]=Default_Handler,[3]=Default_Handler,[4]=Default_Handler,
 [5]=Default_Handler,[6]=Default_Handler,[11]=Default_Handler,
 [12]=Default_Handler,[14]=Default_Handler,[15]=SysTick_Handler,
 [56]=EXTI15_10_IRQHandler
};
/* Freestanding compiler aggregate helpers. */
void *memset(void *d,int v,unsigned int n){u8 *p=d;while(n--)*p++=(u8)v;return d;}
void *memcpy(void *d,const void *s,unsigned int n){u8 *p=d;const u8 *q=s;while(n--)*p++=*q++;return d;}
