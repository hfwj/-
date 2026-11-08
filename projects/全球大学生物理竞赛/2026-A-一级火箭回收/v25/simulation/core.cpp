#include <cmath>
#include <algorithm>
#include <array>
#include "config.h"
using S=std::array<double,11>;
constexpr double PI=3.14159265358979323846;
struct Ctx {int phase=0,engines=0,mode=1;bool fullq=false;double ready=0,pars[4];};
struct Diag {double rho,cd,q,pd,area,fx,fz,thrust,tx,tz,n,phi_cmd,throttle_cmd,need;};
static double clamp(double x,double lo,double hi){return std::max(lo,std::min(hi,x));}
static double wrap(double x){return std::remainder(x,2*PI);}
static double interp(double x,const double*xx,const double*yy,int n){
 if(x<=xx[0])return yy[0];if(x>=xx[n-1])return yy[n-1];
 int j=0;while(j<n-2 && x>xx[j+1])++j;
 return yy[j]+(yy[j+1]-yy[j])*(x-xx[j])/(xx[j+1]-xx[j]);
}
static void lower_atmo(double h,double &rho,double &sound){
 const double hb[]={0,11000,20000,32000,47000,51000,71000,84852};
 const double lapse[]={-.0065,0,.001,.0028,0,-.0028,-.002};
 double H=RA*std::max(0.,h)/(RA+std::max(0.,h)),T=288.15,P=101325.;
 for(int j=0;j<7;j++){
  double top=std::min(H,hb[j+1]),dh=std::max(0.,top-hb[j]),T1=T+lapse[j]*dh;
  P*=std::abs(lapse[j])<1e-12?std::exp(-G0*dh/(R_AIR*T)):std::pow(T/T1,G0/(R_AIR*lapse[j]));
  T=T1;if(H<=hb[j+1])break;
 }
 rho=P/(R_AIR*T);sound=std::sqrt(GAMMA_AIR*R_AIR*T);
}
static void atmosphere(double h,double&rho,double&sound){
 lower_atmo(std::min(h,86000.),rho,sound);
 if(h>86000.)rho*=std::exp(-(h-86000.)/HIGH_H);
}
static double contact_height(const S&y){
 double tilt=wrap(y[5]-PI/2);return FOOT_LENGTH*std::cos(tilt)+FOOT_SPAN*std::abs(std::sin(tilt));
}
static Diag diagnose(double t,const S&y,const Ctx&c){
 Diag d{};double h=std::max(0.,y[1]),r=RE+h,m=std::max(y[4],DRY),sound;
 atmosphere(h,d.rho,sound);
 double wind=interp(h,WIND_H,WIND_U,8),vrx=y[2]-wind,vrz=y[3],va=std::hypot(vrx,vrz);
 d.cd=interp(va/sound,CD_M,CD_Y,12);d.q=.5*d.rho*va*va;d.pd=d.q*d.cd;
 double alpha=wrap(y[5]-std::atan2(vrz,vrx));
 d.area=PI*DIAMETER*DIAMETER/4; // Fixed effective axial-area closure; no uncalibrated broadside law.
 d.fx=-d.pd*d.area*vrx/std::max(va,1e-12);d.fz=-d.pd*d.area*vrz/std::max(va,1e-12);
 bool entry=c.phase==2,land=c.phase==5,burning=entry||land;
 d.phi_cmd=std::atan2(-vrz,-vrx);d.throttle_cmd=0;d.need=0;
 if(c.phase>=3 && c.phase<=5){
  double clear=std::max(y[1]-contact_height(y),CLEAR_FLOOR),down=std::max(-y[3],0.);
  double tgo=std::max(2*clear/(down+c.pars[3]),TGO_FLOOR);
  double ax=-KX*y[2]/tgo+y[2]*y[3]/r;
  double az=((y[3]<=0?y[3]*y[3]:-y[3]*y[3])-c.pars[3]*c.pars[3])/(2*clear)+MU/(r*r)-y[2]*y[2]/r;
  double reqx=m*ax-d.fx,reqz=m*az-d.fz;
  double limit=(TILT_LOW_DEG+(TILT_HIGH_DEG-TILT_LOW_DEG)*std::min(clear/TILT_HEIGHT,1.))*PI/180;
  d.need=std::hypot(reqx,reqz);d.phi_cmd=clamp(std::atan2(reqz,reqx),PI/2-limit,PI/2+limit);
 }
 if(burning){
  double wanted=entry?c.engines*ENGINE_T:d.need;
  if(land && c.fullq)wanted=c.engines*ENGINE_T*THROTTLE_MAX;
  // Limit estimated resultant non-gravitational acceleration, with margin.
  double nx=std::cos(d.phi_cmd),nz=std::sin(d.phi_cmd),proj=d.fx*nx+d.fz*nz;
  double cap2=std::pow(N_CONTROL*m*G0,2)-d.fx*d.fx-d.fz*d.fz+proj*proj;
  double cap=std::max(0.,-proj+std::sqrt(std::max(0.,cap2)));
  wanted=std::min(wanted,cap);
  d.throttle_cmd=clamp(wanted/(c.engines*ENGINE_T),THROTTLE_MIN,THROTTLE_MAX);
  d.thrust=c.engines*ENGINE_T*clamp(y[6],0.,THROTTLE_MAX);
 }
 d.tx=d.thrust*std::cos(y[5]);d.tz=d.thrust*std::sin(y[5]);
 d.n=std::hypot(d.tx+d.fx,d.tz+d.fz)/(m*G0);return d;
}
static S rhs(double t,const S&y,const Ctx&c){
 Diag d=diagnose(t,y,c);double m=std::max(y[4],DRY),r=RE+y[1];S z{};
 z[0]=RE*y[2]/r;z[1]=y[3];z[2]=(d.tx+d.fx)/m-y[2]*y[3]/r;
 z[3]=(d.tz+d.fz)/m-MU/(r*r)+y[2]*y[2]/r;
 z[4]=-d.thrust/(ISP*G0);
 z[5]=clamp(wrap(d.phi_cmd-y[5])/ATT_TAU,-ATT_RATE_DEG*PI/180,ATT_RATE_DEG*PI/180);
 if(c.phase==2 || c.phase==5)z[6]=clamp((d.throttle_cmd-y[6])/ENGINE_TAU,-SLEW,SLEW);
 if(c.phase==2){z[7]=d.tx;z[8]=d.tz;}
 if(c.phase==5){z[9]=d.tx;z[10]=d.tz;}
 return z;
}
static S rk4(double t,const S&y,double dt,const Ctx&c){
 S a=rhs(t,y,c),b{},cc{},d{},z=y,tmp;
 for(int j=0;j<11;j++)tmp[j]=y[j]+dt*a[j]/2;b=rhs(t+dt/2,tmp,c);
 for(int j=0;j<11;j++)tmp[j]=y[j]+dt*b[j]/2;cc=rhs(t+dt/2,tmp,c);
 for(int j=0;j<11;j++)tmp[j]=y[j]+dt*cc[j];d=rhs(t+dt,tmp,c);
 for(int j=0;j<11;j++)z[j]+=dt*(a[j]+2*b[j]+2*cc[j]+d[j])/6;return z;
}
// Event identifiers: contact, exhaustion, entry request/start/cut,
// landing request/start, 7->3 and 3->2 engine staging.
static double guard(int id,double t,const S&y,const Ctx&c){
 Diag d=diagnose(t,y,c);double g=MU/std::pow(RE+y[1],2),m=std::max(y[4],DRY);
 if(id==0)return y[1]-contact_height(y);
 if(id==1)return y[4]-DRY;
 if(id==2)return y[3]<0?y[1]-c.pars[0]:1e9;
 if(id==3 || id==6)return c.ready-t;
 if(id==4){if(c.mode==0)return y[1]-55000.;
  double vu=interp(std::max(0.,y[1]),WIND_H,WIND_U,8);return std::hypot(y[2]-vu,y[3])-c.pars[1];}
 if(id==5){double net=7*ENGINE_T*THROTTLE_MAX/m-g;
  double stop=std::max(0.,y[2]*y[2]+y[3]*y[3]-c.pars[3]*c.pars[3])/(2*std::max(net,.01));
  return std::min((y[1]-contact_height(y)-c.pars[2]*stop)/1e4,(PD_TRIGGER-d.pd)/PD_TRIGGER);}
 if(id==7)return std::max({(y[1]-STAGE3_H)/STAGE3_H,(d.need-STAGE3_REQ)/STAGE3_REQ,(d.thrust-STAGE3_ACT)/STAGE3_ACT});
 if(id==8)return std::max({(y[1]-STAGE2_H)/STAGE2_H,(d.need-STAGE2_REQ)/STAGE2_REQ,(d.thrust-STAGE2_ACT)/STAGE2_ACT});
 if(id==9)return Q_SOFT-d.q;if(id==10)return d.q-Q_SOFT;
 return 1e9;
}
static bool enabled(int id,const Ctx&c){
 if(id==0)return true;if(id==1)return c.phase!=6;
 if(id==2)return c.phase==0;if(id==3)return c.phase==1;if(id==4)return c.phase==2;
 if(id==5)return c.phase==3;if(id==6)return c.phase==4;
 if(id==9)return c.phase==5 && !c.fullq;if(id==10)return c.phase==5 && c.fullq;
 if(id==7)return c.phase==5 && c.engines==7;if(id==8)return c.phase==5 && c.engines==3;return false;
}
extern "C" int simulate(double prop,const double*pars,double dt,int mode,double*out,double*history,int capacity){
 Ctx c;c.mode=mode;for(int j=0;j<4;j++)c.pars[j]=pars[j];
 S y{};y[1]=H0;y[2]=V0*std::cos(GAMMA0_DEG*PI/180);y[3]=V0*std::sin(GAMMA0_DEG*PI/180);y[4]=DRY+prop;y[5]=std::atan2(-y[3],-y[2]);
 double t=0,entry_start_mass=0,entry_used=0,qmax=0,nmax=0,apogee=H0;
 double events[11];for(double&v:events)v=-1;
 double entry_max=0,land_max=0;int stored=0,steps=0,status=0;
 auto record=[&](){Diag d=diagnose(t,y,c);qmax=std::max(qmax,d.q);nmax=std::max(nmax,d.n);apogee=std::max(apogee,y[1]);
  if(c.phase==2)entry_max=std::max(entry_max,d.thrust);if(c.phase==5)land_max=std::max(land_max,d.thrust);
  if(history && stored<capacity){double*row=history+stored*18;row[0]=t;for(int j=0;j<7;j++)row[j+1]=y[j];
   row[8]=d.q;row[9]=d.n;row[10]=d.thrust;row[11]=c.phase;row[12]=c.engines;row[13]=d.fx;row[14]=d.fz;row[15]=d.area;row[16]=d.pd;row[17]=std::hypot(y[2],y[3]);stored++;}};
 auto process=[&](int id){events[id]=t;
  if(id==0){status=1;return;}
  if(id==1){if(c.phase==2)entry_used=entry_start_mass-DRY;y[4]=DRY;y[6]=0;c.phase=6;c.engines=0;return;}
  if(id==2){c.phase=1;c.ready=t+IGN_DELAY;return;}
  if(id==3){c.phase=2;c.engines=7;y[5]=diagnose(t,y,c).phi_cmd;y[6]=0;entry_start_mass=y[4];return;}
  if(id==4){entry_used=entry_start_mass-y[4];c.phase=3;c.engines=0;y[6]=0;return;}
  if(id==5){c.phase=4;c.ready=t+IGN_DELAY;return;}
  if(id==6){c.phase=5;c.engines=7;y[6]=0;c.fullq=diagnose(t,y,c).q>=Q_SOFT;if(c.fullq)events[9]=t;return;}
  if(id==7){c.engines=3;return;}
  if(id==8){c.engines=2;return;}
  if(id==9){c.fullq=true;return;}if(id==10){c.fullq=false;return;}};
 record();
 while(t<900 && steps++<2000000 && !status){
  // Handle a guard already active at an accepted state.
  int immediate=-1;for(int id=0;id<9;id++)if(enabled(id,c) && guard(id,t,y,c)<=1e-9){immediate=id;break;}
  if(immediate>=0){process(immediate);record();continue;}
  double step=std::min(dt,900-t);S trial=rk4(t,y,step,c);double earliest=step+1;int hit=-1;
  for(int id=0;id<11;id++)if(enabled(id,c)){
   double a=guard(id,t,y,c),b=guard(id,t+step,trial,c);
   if(a>0 && b<=0){double lo=0,hi=step;
    for(int k=0;k<30;k++){double mid=(lo+hi)/2;S z=rk4(t,y,mid,c);if(guard(id,t+mid,z,c)>0)lo=mid;else hi=mid;}
    double at=(lo+hi)/2;if(at<earliest){earliest=at;hit=id;}}
  }
  if(hit>=0){y=rk4(t,y,earliest,c);t+=earliest;process(hit);}else{y=trial;t+=step;}
  record();
 }
 if(c.phase==2 && !entry_used)entry_used=entry_start_mass-y[4];
 double used=DRY+prop-y[4],tilt=std::abs(wrap(y[5]-PI/2))*180/PI;
 bool pass=status==1 && events[1]<0 && y[3]<=0 && -y[3]<=VZ_LIMIT && std::abs(y[2])<=VX_LIMIT && tilt<=TILT_LIMIT_DEG && qmax<=Q_LIMIT && nmax<=N_LIMIT && y[4]-DRY>=RESERVE;
 out[0]=pass;out[1]=used;out[2]=entry_used;out[3]=used-entry_used;out[4]=y[2];out[5]=y[3];out[6]=qmax;out[7]=nmax;out[8]=tilt;out[9]=t;out[10]=y[0];out[11]=apogee;out[12]=y[4]-DRY;out[13]=status;
 for(int j=0;j<9;j++)out[14+j]=events[j];out[23]=entry_max;out[24]=land_max;
 for(int j=0;j<4;j++)out[25+j]=y[7+j];out[29]=steps;out[30]=events[9];out[31]=events[10];return stored;
}
