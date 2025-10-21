# Using R to convert an RData file to a CSV file, so that code can be written using Python

load("./data/compustat_clean.Rdata")
load("./data/FDIC_resources_clean.Rdata")
object_names_compustat <- load("./data/compustat_clean.Rdata")
object_names_fdic <- load("./data/FDIC_resources_clean.Rdata")

# printing the object names to identify the data frame
print(object_names_compustat)
print(object_names_fdic)

write.csv(
  x = compustat, 
  file = paste0("./data/", "compustat_clean.csv"),
  row.names = FALSE 
)
write.csv(
  x = FDIC_resources,
  file = paste0("./data/", "FDIC_clean.csv"),
  row.names = FALSE
)

q("no")

