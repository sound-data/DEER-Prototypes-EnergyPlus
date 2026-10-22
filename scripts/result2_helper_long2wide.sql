with ColumnUnits as (
SELECT distinct "ColumnName", "Units"
FROM "sim_tabular"
)
SELECT
st.filename,
cu."ColumnName" || " (" || cu."Units" || ")" as "ColumnUnits",
sum(Value) as "Value"
from sim_tabular st
join ColumnUnits cu
on st."ColumnName" = cu."ColumnName"
group by st.filename, cu."ColumnName";
