#!/usr/bin/env Rscript
# scripts/run_fsqca.R
# Rscript wrapper that runs QCA and emits JSON to stdout

suppressPackageStartupMessages({
  library(jsonlite)
  library(QCA)
})

args <- commandArgs(trailingOnly=TRUE)
if(length(args) < 2){
  cat(toJSON(list(error="usage: run_fsqca.R /path/to/input.json job_id"), auto_unbox=TRUE))
  quit(status=1)
}

input_path <- args[1]
job_id <- args[2]

# Read input
inp <- tryCatch({
  fromJSON(input_path)
}, error = function(e){
  cat(toJSON(list(job_id=job_id, status="error", error=as.character(e)), auto_unbox=TRUE))
  quit(status=2)
})

# Expect inp$cases as an array-of-objects; convert to data.frame
if(is.null(inp$cases) || is.null(inp$config)){
  cat(toJSON(list(job_id=job_id, status="error", error="missing cases or config"), auto_unbox=TRUE))
  quit(status=3)
}

cases_df <- as.data.frame(inp$cases, stringsAsFactors=FALSE)
cfg <- inp$config

# Defensive: ensure outcome and conditions exist
outcome <- cfg$outcome
conditions <- cfg$conditions
incl_cut <- ifelse(is.null(cfg$incl.cut), 0.5, cfg$incl.cut)
mode <- ifelse(is.null(cfg$mode), "crisp", cfg$mode)

if(!(outcome %in% colnames(cases_df))){
  cat(toJSON(list(job_id=job_id, status="error", error=paste("outcome not found:", outcome)), auto_unbox=TRUE))
  quit(status=4)
}

# Build truth table
# QCA::truthTable expects a data.frame with factors/numeric 0/1 for crisp
# Wrap in tryCatch to surface errors
res <- tryCatch({
  # For fuzzy, user should provide values between 0 and 1; for crisp use 0/1
  tt <- truthTable(cases_df, outcome = outcome, conditions = conditions, incl.cut = incl_cut, use.letters = FALSE)
  # minimize / intermediate solution; for crisp we can use minimize
  sol <- minimize(tt, details = TRUE)

  # Prepare diagnostics - many are embedded in returned objects
  diagnostics <- list()
  # Attempt to extract basic measures if present
  # Note: QCA package returns complex objects; we include placeholders and raw dumps
  out <- list(
    job_id = job_id,
    status = "ok",
    solutions = sol$solution,
    truth_table = tt$tt, # raw truth table matrix/data
    details = sol$details,
    diagnostics = diagnostics,
    qca_package_version = as.character(packageVersion("QCA"))
  )
  out
}, error = function(e){
  list(job_id = job_id, status = "error", error = as.character(e))
})

cat(toJSON(res, auto_unbox=TRUE, null="null"))
quit(status=0)
