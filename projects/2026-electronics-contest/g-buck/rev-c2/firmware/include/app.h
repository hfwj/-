#ifndef APP_H
#define APP_H
#include "config.h"
typedef unsigned int u32;
typedef unsigned short u16;
typedef unsigned char u8;
typedef signed int i32;
typedef enum {OFF, PRECHARGE, READY, ARMING, SOFTSTART, RUN, TRIPPED} State;
typedef enum {F_NONE, F_HARDWARE, F_ADC, F_INPUT, F_OC, F_LOW_OUTPUT, F_OV, F_TIMING} Fault;
typedef struct {i32 vin, iin, vout, iout, il, vin_post; u8 valid;} Sample;
typedef struct {
 State state; Fault fault;
 u32 age, oc_ms, uv_ms, pre_ms;
 i32 vset, iset, cv, cc, cv_rem, cc_rem, ev_old, ei_old, duty;
 u8 bypass_confirmed, enable, arm, cc_mode, edit_current;
} App;
typedef enum {CMD_NONE, CMD_PRECHARGE, CMD_CONFIRM_BYPASS, CMD_START, CMD_STOP,
 CMD_SET_V, CMD_SET_I} Command;
void app_init(App *a);
void app_trip(App *a, Fault f);
void app_command(App *a, Command c, i32 value);
void app_tick(App *a, const Sample *s, u8 fault_n, u8 oc_n);
void adc_convert(const u16 raw[6], Sample *s);
/* Calibration: output = (nominal + offset) * gain_ppm / 1e6.
 * Applied separately to each channel, including signed IL. */
extern i32 adc_offset[6], adc_gain_ppm[6];
#endif
