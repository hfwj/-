const fs=require('fs'),path=require('path');
const {validateFormat,validateOuter}=require(path.join(process.argv[3], 'validate.js'));
const root=process.argv[2];let count=0,errors=[];
function scan(dir){for(const f of fs.readdirSync(dir)){const p=path.join(dir,f);if(fs.statSync(p).isDirectory())scan(p);else if(/\.(esch2|ecfg)$/.test(f)){let doc='';for(const [i,line] of fs.readFileSync(p,'utf8').trim().split('\n').entries()){const j=line.indexOf('||'),a=JSON.parse(line.slice(0,j)),b=JSON.parse(line.slice(j+2).replace(/\|$/,''));if(a.type==='DOCHEAD')doc=b.docType;const outer=validateOuter(a);let inner=a.type==='DOCHEAD'?{valid:true,errors:[]}:validateFormat(a.type,b,doc);count++;if(!outer.valid||!inner.valid)errors.push({file:f,line:i+1,type:a.type,doc,errors:[...outer.errors,...inner.errors]});}}}}
scan(root);const out={valid:errors.length===0,records:count,errors};console.log(JSON.stringify(out,null,2));if(errors.length)process.exit(1);
