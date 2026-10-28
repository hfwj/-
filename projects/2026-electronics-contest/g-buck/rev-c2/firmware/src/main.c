#include "board.h"
static App app;
static Sample sample;
static volatile u32 ticks, hard_fault;
/* SWD debugger mailbox: write value first, command last. Cleared on consumption.
 * No power activation is possible in the default interlocked build. */
volatile u32 debug_command;
volatile i32 debug_value;
volatile App debug_status;
volatile Sample debug_sample;
u32 millis(void){return ticks;}
void delay_ms(u32 ms){u32 start=ticks;while(ticks-start<ms){__asm volatile("nop");}}
static void lock(void){__asm volatile("cpsid i":::"memory");}
static void unlock(void){__asm volatile("cpsie i":::"memory");}
void EXTI15_10_IRQHandler(void){
 if(REG(0x40010414)&(1u<<10)){
  board_kill();hard_fault=1;REG(0x40010414)=1u<<10;
 }
}
void SysTick_Handler(void){
 u32 start=REG(0xE0001004);static u32 previous;
 ticks++;
 if(previous && start-previous>CPU_HZ/1000*2){app_trip(&app,F_TIMING);}
 previous=start;
 u16 raw[6];u8 good=board_sample(raw);
 if(good)adc_convert(raw,&sample);else sample.valid=0;
 /* Mailbox dispatch and all App mutations occur only here. */
 Command cmd=(Command)debug_command;i32 value=debug_value;debug_command=0;
 if(cmd==CMD_PRECHARGE && (REG(GPIOB+8)&(1u<<10))){
  lock();
  /* A pending falling edge must not be erased by a simultaneous manual ARM. */
  if(!(REG(0x40010414)&(1u<<10)))hard_fault=0;
  unlock();
 }
 app_command(&app,cmd,value);
 keys_tick(&app);
 if(hard_fault)app_trip(&app,F_HARDWARE);
 else app_tick(&app,&sample,(REG(GPIOB+8)&(1u<<10))!=0,(REG(GPIOB+8)&(1u<<11))!=0);
 if(REG(0xE0001004)-start>CPU_HZ/1000)app_trip(&app,F_TIMING);
 lock();
 if(hard_fault || !(REG(GPIOB+8)&(1u<<10)) || (REG(0x40010414)&(1u<<10)))
  app_trip(&app,F_HARDWARE);
 board_outputs(&app);
 debug_status=app;debug_sample=sample;
 unlock();
}
int main(void){
 app_init(&app);
 REG(0xE000EDFC)|=1u<<24;REG(0xE0001000)|=1; /* DWT cycle counter */
 board_init();
 lcd_init();
 /* Start watchdog after the deliberately long LCD reset/sleep-out sequence. */
 REG(0x40003000)=0x5555;REG(0x40003004)=3;REG(0x40003008)=312;
 REG(0x40003000)=0xAAAA;REG(0x40003000)=0xCCCC;
 for(;;){
  App a;Sample s;
  lock();a=app;s=sample;unlock();
  lcd_update(&a,&s);
  /* Only the foreground feeds watchdog: blocked display also forces a reset. */
  REG(0x40003000)=0xAAAA;
  delay_ms(50);
 }
}
