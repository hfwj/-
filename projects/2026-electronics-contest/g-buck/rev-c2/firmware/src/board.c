#include "board.h"
static void pin(u32 port,u32 n,u32 mode){
 u32 address=port+(n<8?0:4),shift=(n%8)*4;
 REG(address)=(REG(address)&~(15u<<shift))|(mode<<shift);
}
void board_kill(void){REG(GPIOB+0x14)=1;REG(TIM1+0x44)&=~(1u<<15);REG(TIM1+0x34)=0;}
void board_init(void){
 /* Internal HSI 8MHz -> PLL 64MHz, APB1 32MHz, ADC 8MHz. No crystal assumption. */
 REG(RCC)|=1;while(!(REG(RCC)&2)){}
 REG(0x40022000)=0x12; /* flash prefetch, two wait states */
 REG(RCC+4)=(14u<<18)|(4u<<8)|(3u<<14);
 REG(RCC)|=1u<<24;while(!(REG(RCC)&(1u<<25))){}
 REG(RCC+4)|=2;while((REG(RCC+4)&12)!=8){}
 REG(RCC+0x18)|=(1u<<0)|(1u<<2)|(1u<<3)|(1u<<9)|(1u<<11)|(1u<<12);
 REG(GPIOB+0x14)=3; /* EN, ARM low BEFORE switching pin mode */
 pin(GPIOB,0,2);pin(GPIOB,1,2);
 for(u32 n=0;n<5;n++)pin(GPIOA,n,0);
 pin(GPIOA,6,0);
 /* External board pullups are expected; internal pullups also enabled. */
 REG(GPIOB+0x10)=(1u<<10)|(1u<<11);
 pin(GPIOB,10,8);pin(GPIOB,11,8);
 pin(GPIOA,8,0xA); /* TIM1_CH1, AF push-pull */
 REG(TIM1+0x28)=0;REG(TIM1+0x2C)=PWM_PERIOD-1;
 REG(TIM1+0x34)=0;REG(TIM1+0x18)=(6u<<4)|(1u<<3);
 REG(TIM1+0x20)=1; /* CH1 only; IR2184 generates complementary signals/dead time */
 REG(TIM1+0x44)=0;REG(TIM1+0x14)=1;REG(TIM1)=0x81;
 /* EXTI10 falling edge, highest priority. Do not EXTI-latch PB11 OC. */
 REG(0x40010010)=(REG(0x40010010)&~(15u<<8))|(1u<<8);
 REG(0x40010400)|=1u<<10;REG(0x4001040C)|=1u<<10;
 REG(0x40010414)=1u<<10;
 *(volatile u8 *)(0xE000E400u+40u)=0;
 REG(0xE000E104)=1u<<8; /* EXTI15_10 IRQ40 */
 REG(ADC1+0x0C)=7u<<18; /* 239.5 cycle acquisition channels 0..6 */
 for(u32 n=0;n<5;n++)REG(ADC1+0x0C)|=7u<<(n*3);
 REG(ADC1+8)=1;for(volatile u32 n=0;n<1000;n++){}
 REG(ADC1+8)|=8;while(REG(ADC1+8)&8){}
 REG(ADC1+8)|=4;while(REG(ADC1+8)&4){}
 REG(ADC1+8)|=(7u<<17)|(1u<<20); /* software trigger enabled */
 /* SysTick 1kHz at lower priority than hardware fault EXTI. */
 *(volatile u8 *)0xE000ED23u=0x80;
 REG(0xE000E014)=CPU_HZ/1000-1;REG(0xE000E018)=0;REG(0xE000E010)=7;

}
u8 board_sample(u16 raw[6]){
 static const u8 channels[6]={0,1,2,3,4,6};
 for(u32 n=0;n<6;n++){
  REG(ADC1)=0;REG(ADC1+0x34)=channels[n];REG(ADC1+8)|=1u<<22;
  u32 timeout=20000;while(!(REG(ADC1)&2) && --timeout){}
  if(!timeout)return 0;
  raw[n]=(u16)REG(ADC1+0x4C);
 }
 return 1;
}
void board_outputs(const App *a){
 /* Called with interrupts masked, after checking sticky EXTI fault. */
 if(!a->enable || !POWER_STAGE_ALLOWED){board_kill();}
 else{
  REG(TIM1+0x34)=(u32)a->duty*PWM_PERIOD/10000;
  REG(TIM1+0x44)|=1u<<15;REG(GPIOB+0x10)=1;
 }
 if(a->arm && POWER_STAGE_ALLOWED)REG(GPIOB+0x10)=2;else REG(GPIOB+0x14)=2;
}
