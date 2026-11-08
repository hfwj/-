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
