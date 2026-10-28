#ifndef CONFIG_H
#define CONFIG_H
/* Bench interlock: the delivered image cannot enable the driver. */
#ifndef POWER_STAGE_ALLOWED
#define POWER_STAGE_ALLOWED 0
#endif
#ifndef KEYS_ENABLED
#define KEYS_ENABLED 0
#endif
#ifndef LCD_ENABLED
#define LCD_ENABLED 1
#endif
#define CPU_HZ 64000000u
#define PWM_PERIOD 2133u /* TIM1 64MHz / 2133 = 30004.7 Hz */
#define ADC_VDDA_MV 3300
#define LCD_WIDTH 128
#define LCD_HEIGHT 160
#define LCD_X_OFFSET 0
#define LCD_Y_OFFSET 0
#define LCD_MADCTL 0x00 /* module-specific RGB/BGR + rotation */
#define DUTY_MAX 8500 /* basis points; 85%, preserves bootstrap refresh */
#define SOFTSTART_MS 300u
#define PRECHARGE_MS 100u
#define OC_DELAY_MS 20u
#define UV_DELAY_MS 20u
#define VIN_MIN_MV 12000
#define VIN_MAX_MV 27000
/* Conservative starting gains, NOT tuned on the actual power stage.
 * Incremental PI: duty_bp += kp*(err-previous_err) + ki*err.
 * Gains below are scaled by 1000; error is mV or mA, step is 1ms. */
#define CV_KP 100
#define CV_KI 2
#define CC_KP 500
#define CC_KI 10
#endif
