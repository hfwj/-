/* R7 wiring reference only. No complete firmware/build/hardware test is supplied.
 * Core: User-selected STM32F103C8T6 Blue Pill (upper USB-end contact GND).
 * GPIO and ADC assignment is unchanged from R6. Migration notes below concern R5.
 * If using STM32F1 HAL include stm32f1xx_hal.h before this file.
 * ADC sequencer/DMA: replace the former voltage ADC_CHANNEL_0 with ADC_CHANNEL_2;
 * retain current ADC_CHANNEL_1 and update scan order/buffer interpretation together.
 * KEY_DOWN requires GPIOB clock and PB10 input, replacing PA11.
 * Use HSI or explicitly configure and verify clocks; ADC clock must meet ST limits.
 */
#ifndef GBUCK_PINMAP_R7_H
#define GBUCK_PINMAP_R7_H
#define VOUT_ADC_GPIO_Port GPIOA
#define VOUT_ADC_Pin GPIO_PIN_2
#define VOUT_ADC_Channel ADC_CHANNEL_2
#define ISENSE_GPIO_Port GPIOA
#define ISENSE_Pin GPIO_PIN_1
#define ISENSE_Channel ADC_CHANNEL_1
#define RUN_GPIO_Port GPIOA
#define RUN_Pin GPIO_PIN_8
#define KEY_SET_GPIO_Port GPIOA
#define KEY_SET_Pin GPIO_PIN_9
#define KEY_UP_GPIO_Port GPIOA
#define KEY_UP_Pin GPIO_PIN_10
#define KEY_DOWN_GPIO_Port GPIOB
#define KEY_DOWN_Pin GPIO_PIN_10
#define LCD_CE_GPIO_Port GPIOA
#define LCD_CE_Pin GPIO_PIN_4
#define LCD_CLK_GPIO_Port GPIOA
#define LCD_CLK_Pin GPIO_PIN_5
#define LCD_DIN_GPIO_Port GPIOA
#define LCD_DIN_Pin GPIO_PIN_7
#define LCD_DC_GPIO_Port GPIOB
#define LCD_DC_Pin GPIO_PIN_0
#define LCD_RST_GPIO_Port GPIOB
#define LCD_RST_Pin GPIO_PIN_1
#define SCL_GPIO_Port GPIOB
#define SCL_Pin GPIO_PIN_6
#define SDA_GPIO_Port GPIOB
#define SDA_Pin GPIO_PIN_7
/* PCD8544, 84x48, 3.3V. LCD CE must be software-controlled if NSS is not enabled.
 * Keys are active low. Set RUN low before enabling outputs and control functions.
 * PA0 stays unused on the carrier to retain the R6 firmware mapping.
 * The debug header is P3 ON THE MODULE: 1 VTref, 2 SWDIO, 3 SWCLK, 4 GND.
 */
#endif
