# R script to query REST-API from empirica-systeme, see https://www.empirica-systeme.de/en/portfolio/empirica-systeme-rest-api/
# This work is licensed under a "Creative Commons Attribution 4.0 International License", sett http://creativecommons.org/licenses/by/4.0/
# Documentation of REST-API at https://api.empirica-systeme.de/api-docs/

# required R-packages
library(httr)
library(jsonlite)
library(dplyr)

####################################################################################################
# USER INPUT
# your chosen data will be avalaible in df 'data'
####################################################################################################

# set pw and username
username <- "###" 
password <- "###" 


##################################################
# choose segment (or any other filter)
# copy OR define JSON between without initial { and final } ###
base_json <- paste('
                     {
                     "segment" : "WHG_M",
                     "administrativeSpatialFilter" : {
                     "municipalityCodes" : [11000000,2000000]
                     }
                     }
                     ')

##################################################
# choose endpoint according to swagger without initial / , see https://api.empirica-systeme.de/api-docs/
endpoint <- 'aggregated/kosten_je_flaeche/MEDIAN'



####################################################################################################
####################################################################################################
# DON'T CHANGE  
####################################################################################################
####################################################################################################
  
# PULL POST
  
id <- POST("https://api.empirica-systeme.de/queries", body = fromJSON(paste0(base_json)), encode = "json", authenticate(username,password, type = "basic"))
  
  
get_id <- content(id, "text")
get_id_json <- fromJSON(get_id, flatten = TRUE)
  
##################################################
  
# GET REQUEST

base <- paste0("https://api.empirica-systeme.de/results/",get_id_json$queryId)
    
# get endpoints you need
    
call <- paste(base,"/",endpoint,sep="")
    
    
##################################################
    
# get data
 
get_data <- GET(call, authenticate(username,password, type = "basic"))
 
# get object
    
get_data_text <- content(get_data, "text")
    
# return object into JSON
    
get_data_json <- fromJSON(get_data_text, flatten = TRUE)
    
##################################################
    
# return data in dataframe
    
data <- as.data.frame(get_data_json)
    
