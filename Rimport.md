# R Import

Before starting, please make sure that you only try to read config and log files that belong together. That is, if you changed your config file over time but did not empty/delete the log files accordingly (i.e., parts of the log file do not match the read config file), this import script will not find meaningful things. Moreover, make sure that *jsonlite* is installed.

Now, let's start.

First, this script needs to know the ScrapeBot's main directory. In addition, some settings may be specified here as well:
```{r basic settings}
dir.prefix <- choose.dir()
dir.config <- '/config/'
dir.log <- '/log/'
#install.packages('jsonlite')
```

Second, configuration files are loaded in order to have an initial overview of what is available. This is mandatory for all other steps.
```{r load config files}
cConfig <- list.files(paste0(dir.prefix, dir.config), '^.+(.json)$')
cConfig <- substr(cConfig, 0, nchar(cConfig) - 5)
sprintf('Total amount of config files: n = %d', length(cConfig))
```

## Single data Collection
Third, the data can be loaded. Yet, it is located in multiple storage points:
* The bot.log file includes the times each configuration was run.
* Each configuration's log file includes information on, for instance, randomly chosen URLs.
* Each configuration's eval log file includes evaluated information.

Not every installation needs every data collection. So, please choose wisely which code to run here.

### Configuration runtime statistics
```{r load runtime data from bot.log}
oBotLog <- file(paste0(dir.prefix, dir.log, 'bot.log'), 'r')
cConfigCount <- c(table(readLines(oBotLog)))
close(oBotLog)
rm(oBotLog)
sprintf('Runtimes per config file: M = %.1f; SD = %.2f', mean(cConfigCount), sd(cConfigCount))
```

### Single runs per configuration file
```{r load all runs per configuration log}
splitTimeFromText <- function(sLine) {
  cLine <- strsplit(sLine, ' ', fixed=T)[[1]]
  bContainsStep <- ifelse(substr(cLine[7], 1, 1) == '[' & substr(cLine[7], nchar(cLine[7]), nchar(cLine[7])) == ']', T, F)
  return(list(
    dTime = as.POSIXct(strptime(paste(cLine[1:5], collapse=' '), '%a %b %d %H:%M:%S %Y'), tz='GMT'),
    nStep = ifelse(bContainsStep, as.numeric(substr(cLine[7], 2, nchar(cLine[7]) - 1)), NA),
    sText = paste(cLine[ifelse(bContainsStep, 8, 7):length(cLine)], collapse=' ')
  ))
}
findRunDateForLogDate <- function(dLog, cRun) {
  dClosestStart <- NA
  sapply(cRun, function(dStart) {
    if(dStart <= dLog & (is.na(dClosestStart) | dStart > dClosestStart)) {
      dClosestStart <<- dStart
    }
  })
  if(is.na(dClosestStart)) {
    warning('No run date found for log date.')
  }
  return(dClosestStart)
}

lRunLog <- list()
sTempLocale <- Sys.getlocale('LC_TIME')
Sys.setlocale('LC_TIME', 'English')
sapply(names(cConfigCount), function(sConfig) {
  sFilename <- paste0(dir.prefix, dir.log, sConfig, '.txt')
  if(file.exists(sFilename)) {
    oConfigLog <- file(sFilename, 'r')
    aLine <- readLines(oConfigLog)
    #run through config log file's lines
    for(sLine in aLine) {
      if(sLine != '') {
        lLine <- splitTimeFromText(sLine)
        if(!is.na(lLine[['nStep']]) & lLine[['nStep']] == 0) {
          #if first step, create new DF for this run
          lRunLog[[sConfig]] <<- data.frame(dStart=lLine[['dTime']], s0=lLine[['sText']])
        } else if(!is.na(lLine[['nStep']])) {
          #if not first step, eventually create this step's column
          if(!(paste0('s', lLine[['nStep']]) %in% colnames(lRunLog[[sConfig]]))) {
            lRunLog[[sConfig]] <<- cbind(lRunLog[[sConfig]], NA)
            colnames(lRunLog[[sConfig]])[ncol(lRunLog[[sConfig]])] <<- paste0('s', lLine[['nStep']])
          }
          #find runtime that is closest (parent) to the current found log line and write log text to this run DF
          dClosestStart <- findRunDateForLogDate(lLine[['dTime']], lRunLog[[sConfig]]$dStart)
          if(!is.na(dClosestStart)) {
            lRunLog[[sConfig]][lRunLog[[sConfig]]$dStart == dClosestStart, paste0('s', lLine[['nStep']])] <<- lLine[['sText']]
          }
        }
      }
    }
    close(oConfigLog)
  } else {
    lRunLog[[sConfig]] <<- data.frame()
  }
})
Sys.setlocale('LC_TIME', sTempLocale)
rm(sTempLocale)
```

### Configuration eval history
For this to be read, jsonlite package has to be installed.

```{r load eval logfiles}
library(jsonlite)
lRunEval <- list()
sTempLocale <- Sys.getlocale('LC_TIME')
Sys.setlocale('LC_TIME', 'English')
sapply(names(cConfigCount), function(sConfig) {
  lRunEval[[sConfig]] <<- list()
  sFilename <- paste0(dir.prefix, dir.log, sConfig, '_eval.json')
  if(file.exists(sFilename)) {
    oConfigEval <- file(sFilename, 'r')
    aLine <- readLines(oConfigEval)
    #run through config eval file's lines
    for(sLine in aLine) {
      lLine <- fromJSON(sLine)
      lLine[['dGMT']] <- as.POSIXct(strptime(paste(strsplit(lLine[['dGMT']], ' ', fixed=T)[[1]][1:5], collapse=' '), '%a, %d %b %Y %H:%M:%S'), tz='GMT')
      if(!(lLine[['nStep']] %in% names(lRunEval[[sConfig]]))) {
        lRunEval[[sConfig]][[paste0('s', lLine[['nStep']])]] <<- NULL
      }
      dClosestStart <- findRunDateForLogDate(lLine[['dGMT']], lRunLog[[sConfig]]$dStart)
      if(!is.na(dClosestStart)) {
        lRunEval[[sConfig]][[paste0('s', lLine[['nStep']])]] <<- rbind(lRunEval[[sConfig]][[paste0('s', lLine[['nStep']])]], cbind(lLine[['aResult']], dStart=dClosestStart))
      }
    }
    close(oConfigEval)
  }
})
Sys.setlocale('LC_TIME', sTempLocale)
rm(sTempLocale)
```
