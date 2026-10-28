#include "board.h"
#if LCD_ENABLED
static void out(u8 byte){
 u32 timeout=100000;while(!(REG(SPI1+8)&2) && --timeout){}
 *(volatile u8 *)(SPI1+0x0C)=byte;
 timeout=100000;while((REG(SPI1+8)&128) && --timeout){}
}
static void cs(u8 high){REG(GPIOB+(high?0x10:0x14))=1u<<12;}
static void command(u8 c){cs(0);REG(GPIOB+0x14)=1u<<13;out(c);cs(1);}
static void data(u8 c){cs(0);REG(GPIOB+0x10)=1u<<13;out(c);cs(1);}
static void window(u16 x,u16 y,u16 w,u16 h){
 u16 x1=x+LCD_X_OFFSET,x2=x1+w-1,y1=y+LCD_Y_OFFSET,y2=y1+h-1;
 command(0x2A);data(x1>>8);data(x1);data(x2>>8);data(x2);
 command(0x2B);data(y1>>8);data(y1);data(y2>>8);data(y2);command(0x2C);
}
/* Original 5x7 font subset, columns low-bit first. */
static const char glyphs[]="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ.-: /";
static const u8 font[][5]={
 {62,81,73,69,62},{0,66,127,64,0},{98,81,73,73,70},{34,65,73,73,54},{24,20,18,127,16},
 {39,69,69,69,57},{60,74,73,73,48},{1,113,9,5,3},{54,73,73,73,54},{6,73,73,41,30},
 {126,17,17,17,126},{127,73,73,73,54},{62,65,65,65,34},{127,65,65,34,28},{127,73,73,73,65},
 {127,9,9,9,1},{62,65,73,73,122},{127,8,8,8,127},{0,65,127,65,0},{32,64,65,63,1},
 {127,8,20,34,65},{127,64,64,64,64},{127,2,12,2,127},{127,4,8,16,127},{62,65,65,65,62},
 {127,9,9,9,6},{62,65,81,33,94},{127,9,25,41,70},{38,73,73,73,50},{1,1,127,1,1},
 {63,64,64,64,63},{31,32,64,32,31},{63,64,56,64,63},{99,20,8,20,99},{7,8,112,8,7},
 {97,81,73,69,67},{0,96,96,0,0},{8,8,8,8,8},{0,54,54,0,0},{0,0,0,0,0},{32,16,8,4,2}
};
static void text(u16 y,const char *str){
 for(u32 x=0;x<LCD_WIDTH/6;x++){
  char c=*str;if(c)str++;
  u32 index=39;for(u32 j=0;glyphs[j];j++)if(glyphs[j]==c){index=j;break;}
  window((u16)(x*6),y,6,8);cs(0);REG(GPIOB+0x10)=1u<<13;
  for(u32 row=0;row<8;row++)for(u32 col=0;col<6;col++){
   u16 pixel=(col<5 && ((font[index][col]>>row)&1))?0xFFFF:0;
   out(pixel>>8);out(pixel);
  }
  cs(1);
 }
}
static void value(u16 y,const char *name,i32 n){
 char b[22];u32 k=0;while(*name && k<10)b[k++]=*name++;
 if(n<0){b[k++]='-';n=-n;}
 n=n>99999?99999:n;
 b[k++]=(char)('0'+n/10000);b[k++]=(char)('0'+n/1000%10);b[k++]='.';
 b[k++]=(char)('0'+n/100%10);b[k++]=(char)('0'+n/10%10);b[k++]=(char)('0'+n%10);b[k]=0;
 text(y,b);
}
void lcd_init(void){
 /* SPI1 transmit-only: PA6 remains ADC input. PA5/PA7 AF push-pull. */
 REG(GPIOA)=(REG(GPIOA)&~0xF0F00000u)|0xB0B00000u;
 REG(GPIOB+4)=(REG(GPIOB+4)&~0x0FFF0000u)|0x02220000u;
 REG(GPIOB+0x10)=(1u<<12)|(1u<<13)|(1u<<14);
 REG(SPI1)=(1u<<15)|(1u<<14)|(1u<<9)|(1u<<8)|(2u<<3)|(1u<<2)|(1u<<6);
 REG(GPIOB+0x14)=1u<<14;delay_ms(20);REG(GPIOB+0x10)=1u<<14;delay_ms(120);
 command(1);delay_ms(150);command(0x11);delay_ms(120);
 command(0x3A);data(5);command(0x36);data(LCD_MADCTL);
 command(0x29);delay_ms(20);
 window(0,0,LCD_WIDTH,LCD_HEIGHT);cs(0);REG(GPIOB+0x10)=1u<<13;
 for(u32 n=0;n<LCD_WIDTH*LCD_HEIGHT;n++){out(0);out(0);}cs(1);
}
void lcd_update(const App *a,const Sample *s){
 static const char *states[]={"OFF","PRECHARGE","READY","ARMING","SOFTSTART","RUN","FAULT"};
 text(0,POWER_STAGE_ALLOWED?"GBUCK C2 BENCH":"GBUCK C2 LOCKED");
 text(16,states[a->state]);
 value(32,"VIN V  ",s->vin);value(44,"IIN A  ",s->iin);
 value(56,"VOUT V ",s->vout);value(68,"IOUT A ",s->iout);
 value(80,"SET V  ",a->vset);value(92,"SET A  ",a->iset);
 value(104,"POST V ",s->vin_post);value(116,"IL A   ",s->il);
 char fault[9]="FAULT 0";fault[6]=(char)('0'+a->fault);text(128,fault);
 text(140,a->bypass_confirmed?"BYPASS CONFIRMED":"CONFIRM BYPASS");
 text(152,KEYS_ENABLED?(a->edit_current?"EDIT: CURRENT":"EDIT: VOLTAGE"):"SWD CONTROL");
}
#else
void lcd_init(void){}
void lcd_update(const App *a,const Sample *s){(void)a;(void)s;}
#endif
