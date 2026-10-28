#ifndef BOARD_H
#define BOARD_H
#include "app.h"
#define REG(a) (*(volatile u32 *)(a))
#define RCC 0x40021000u
#define GPIOA 0x40010800u
#define GPIOB 0x40010C00u
#define TIM1 0x40012C00u
#define ADC1 0x40012400u
#define SPI1 0x40013000u
void board_init(void);
u8 board_sample(u16 raw[6]);
void board_outputs(const App *a);
void board_kill(void);
void delay_ms(u32 ms);
u32 millis(void);
void lcd_init(void);
void lcd_update(const App *a,const Sample *s);
void keys_tick(App *a);
#endif
