-- For use with result2.py -s -t
-- Extract sizing data table compatible with output from result.py
SELECT
t."TabularDataIndex",
CAST(t."Value" as REAL) as "Value",
t."ReportName",
t."ReportForString",
t."TableName",
t."RowName",
t."ColumnName",	
t."Units",
m."File Name",
m."BldgLoc", 
m."BldgType", 
m."Story", 
m."BldgHVAC", 
m."BldgVint", 
m."TechGroup", 
m."TechType", 
m."TechID"
from sim_metadata m
join sim_tabular t
on t."filename" = m."File Name"
;
