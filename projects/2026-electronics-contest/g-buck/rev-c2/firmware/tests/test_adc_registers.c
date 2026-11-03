/* Host register-model regression, NOT a physical ADC/settling-time test.
 * ADC offsets/channel fields follow ST's stm32f103xb.h (CMSIS device F1).
 * Compile the real board driver with a narrow register-access override.
 */
#define _GNU_SOURCE
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <sys/mman.h>
#include "app.h"

static volatile u32 *mock_reg(u32 address);
#define REG(a) (*mock_reg(a))
#include "../src/board.c"

static int sampling, stalled_channel = -1;
static u32 reads, read_channels[6];
static const u16 inputs[7] = {1675, 12, 1000, 24, 2048, 4095, 1660};
#define DIRECT(a) (*(volatile u32 *)(uintptr_t)(a))

static volatile u32 *mock_reg(u32 address){
 assert((address >= 0x40010000u && address < 0x40024000u) ||
        (address >= 0xE000E000u && address < 0xE0010000u));
 if(address == RCC){
  if(DIRECT(RCC)&1u) DIRECT(RCC)|=2u;
  if(DIRECT(RCC)&(1u<<24)) DIRECT(RCC)|=1u<<25;
 }
 if(address == RCC+4){
  DIRECT(RCC+4)=(DIRECT(RCC+4)&~12u)|((DIRECT(RCC+4)&3u)<<2);
 }
 if(address == ADC1+8) DIRECT(ADC1+8)&=~12u; /* CAL/RSTCAL complete */
 if(sampling && address == ADC1 && (DIRECT(ADC1+8)&(1u<<22))){
  u32 channel=DIRECT(ADC1+0x34)&31u;
  assert(channel<7);
  if((int)channel != stalled_channel){
   DIRECT(ADC1+0x4C)=inputs[channel];
   DIRECT(ADC1+8)&=~(1u<<22);
   DIRECT(ADC1)|=2u;
  }
 }
 if(sampling && address == ADC1+0x4C){
  assert(reads<6);
  read_channels[reads++]=DIRECT(ADC1+0x34)&31u;
  DIRECT(ADC1)&=~2u; /* DR read clears EOC */
 }
 return (volatile u32 *)(uintptr_t)address;
}

int main(void){
 void *a=mmap((void *)(uintptr_t)0x40010000u,0x14000,
              PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0);
 void *b=mmap((void *)(uintptr_t)0xE000E000u,0x2000,
              PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0);
 assert(a!=MAP_FAILED && b!=MAP_FAILED);
 DIRECT(GPIOA)=DIRECT(GPIOA+4)=0x44444444u;
 DIRECT(GPIOB)=DIRECT(GPIOB+4)=0x44444444u;
 board_init();
 /* SMPR2 at +0x10 owns channels 0..9; SMPR1 at +0x0C owns 10..17. */
 for(u32 c=0;c<=6;c++) if(c!=5) assert(((DIRECT(ADC1+0x10)>>(3*c))&7u)==7u);
 assert(((DIRECT(ADC1+0x10)>>15)&7u)==0u); /* PA5 is LCD SCK, not ADC */
 assert(DIRECT(ADC1+0x0C)==0u);
 for(u32 c=0;c<=6;c++) if(c!=5) assert(((DIRECT(GPIOA)>>(4*c))&15u)==0);
 assert(!(DIRECT(TIM1+0x44)&(1u<<15)) && DIRECT(TIM1+0x34)==0);
 u16 raw[6]; const u32 channels[6]={0,1,2,3,4,6};
 sampling=1;
 assert(board_sample(raw));
 assert(reads==6);
 for(u32 i=0;i<6;i++){
  assert(read_channels[i]==channels[i]);
  assert(raw[i]==inputs[channels[i]]);
 }
 Sample s;adc_convert(raw,&s);
 assert(s.valid && s.vin>14000 && s.vin_post>14000);
 reads=0;stalled_channel=0;
 assert(!board_sample(raw) && reads==0);
 munmap(a,0x14000);munmap(b,0x2000);
 puts("PASS: actual board driver SMPR2/channel mapping, analog GPIO, disabled PWM, six-channel reads and ADC timeout (host register model only)");
}
