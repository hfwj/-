local index = 0
local widths = {
 {0.26,0.33,0.09,0.32}, {0.30,0.70}, {0.34,0.14,0.17,0.19,0.16},
 {0.25,0.18,0.21,0.21,0.15}, {0.38,0.15,0.17,0.15,0.15},
 {0.31,0.27,0.42}, {0.24,0.38,0.38}, {0.20,0.12,0.56,0.12},
 {0.07,0.21,0.28,0.44}
}
function Table(tbl)
 index = index + 1
 local w = widths[index]
 if w then
  local specs = {}
  for i,v in ipairs(w) do specs[i] = {pandoc.AlignLeft, v} end
  tbl.colspecs = specs
 end
 return tbl
end
