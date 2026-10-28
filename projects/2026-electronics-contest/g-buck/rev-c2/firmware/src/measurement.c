#include "app.h"
i32 adc_offset[6]={0,0,0,0,0,0};
i32 adc_gain_ppm[6]={1000000,1000000,1000000,1000000,1000000,1000000};
void adc_convert(const u16 raw[6],Sample *s){
 i32 x[6]; s->valid=1;
 for(u32 n=0;n<6;n++){
  if(raw[n]>=4090)s->valid=0;
  /* VIN/VOUT/VIN_POST: 11:1; IIN/IOUT: 1V/A;
   * IL: 0.5V/A around VDDA/2, INA240A1, 25mOhm. */
  if(n==0 || n==2 || n==5)x[n]=(i32)raw[n]*ADC_VDDA_MV*11/4095;
  else if(n==4)x[n]=((i32)raw[n]*ADC_VDDA_MV/4095-ADC_VDDA_MV/2)*2;
  else x[n]=(i32)raw[n]*ADC_VDDA_MV/4095;
  /* 64 bit intermediate prevents calibration multiplication overflow. */
  x[n]=(i32)(((long long)x[n]+adc_offset[n])*adc_gain_ppm[n]/1000000);
 }
 s->vin=x[0];s->iin=x[1];s->vout=x[2];s->iout=x[3];s->il=x[4];s->vin_post=x[5];
 /* ADC disconnected/stuck-at-zero cannot satisfy the arm prerequisites. */
 if(raw[4]<100 || raw[4]>3995)s->valid=0;
}
