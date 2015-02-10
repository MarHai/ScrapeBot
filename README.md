# ScrapeBot
ScrapeBot is a CasperJS-based tool in order to visit, modify, and scrape a defined set of webpages regularly. It was built to automate various web-based tasks and keep track of them.

## Prerequisites
First, you'll need [CasperJS](http://casperjs.org/). Now, [test it](http://docs.casperjs.org/en/latest/quickstart.html). If up and running, you are ready to go.

## Installation
Clone (or download) the latest version of ScrapeBot and add the executable flag to bot.sh:

```
git clone https://github.com/MarHai/ScrapeBot.git
<<<<<<< HEAD
chmod +x ./bot.sh
```

That's it, really. Set up a config file (or use the example one included) and test it:

```
casperjs scrape.js --uid=example
```

Make sure that all necessary directories (config, cookie, log, screenshot) exist and are in place. Please note that _ScrapeBot keeps track of cookies_.

## A bit of description
ScrapeBot consists of two major parts:
* **scrape.js** handles all the actions defined within _one config_ file at _one time_
* **bot.sh** shell script that calls scrape.js with _all available config_ files _regularly_

That means, for starters and in order to test, you just need _scrape.js_. For the productive action, you then only need to call _bot.sh_ regularly (e.g., through a cronjob) which in turn will handle scrape.js calls. The third file, by the way, _public.js_ holds all functions available to scrape.js within the eval step (see below).

### scrape.js
Calls look like one of the following:

```
casperjs scrape.js --uid=123
casperjs scrape.js --uid=123 --width=1024
casperjs scrape.js --uid=123 --timeout=1500
casperjs scrape.js --uid=123 --dir.screenshot=img/
casperjs scrape.js --uid=123 --userAgent="Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"
```

The `uid` parameter (`123` in these examples) has to match a config file within the specified configuration directory (by default, that is `./config/`). The filename there has to be the specified UID and an additional .json (lower case). In our example, the file has to be `./config/123.json`. Also note, that the config file's name must not include whitespace and/or dots.

While the `uid` parameter is obligatory, the others are optional. Optional parameters include
* **width** (default: `1280`) and **height** (`720`) indicating the emulated browser's viewport
* **timeout** (default `800`) defining the time waiting after each action (e.g., page load) in milliseconds
* **dir.prefix** (default: `./`) specifies the directory where all other directories are based
* **dir.config** (`config/`), **dir.cookie** (`cookie/`), **dir.log** (`log/`), and **dir.screenshot** (`screenshot/`) are, each, appended to _dir.prefix_ specifying the single directories necessary (note the ending slash)

Note, that all configuration parameters (except for mandatory uid) may also be specified within each configuration file. The latter overwrites command-line-given parameters.

### bot.sh
This script assumes to be in the exact same place as scrape.js. Moreover, it needs to be executable (`+x`) and have write access to `log/bot.log`. Upon run, the script looks for all available configuration files in `./config/*.json`, merges their UID with the bot-internal log file (`./log/bot.log`) in order to count each config file's amount of runs, and *scrape.js the 5 least-run configuration files*.

Note, that only runs initiated by _bot.sh_ are counted by adding their UID as a single line to `./log/bot.log`.

## Configuration
Each configuration is a JSON file including an `aStep` array of the steps to do and an optional `oConfig` object with the parameters described above (within the _scrape.js_ section). `aStep` needs to have objects as array elements, each representing one step of action. These steps are run through in the given (array) order.

A single step can be one of the following (defined through `eType`, default, if not set, is `open`):

| Type | Description | Options |
|------|-------------|---------|
|click |click a link or button |`sSel`|
|eval  |evaluate JavaScript function (see list below) within called page |`fEval`|
|fill  |fill form (field) |`sSel`, `oValue`, `bSubmit`|
|log   |write into log file |`sText`|
|open  |open URL |`sUrl`|
|random|open one random URL out of an array of URLs |`aUrl`|
|reload|reload current page |_none_|
|shot  |screenshot current page |_none_|

<<<<<<< HEAD
For _eval_, several JavaScript functions are available. Currently, these include the following:
* `extractGoogleResults` extract results from a Google search result page (incl. title, link, and position)
* `extractDuckDuckGoResults` same for DuckDuckGo.com
* `extractBingResults` same for Microsoft's Bing search
* `extractTweets` extracts a list of Tweets including text, direct Tweet link, author, and position as out of Twitter's default stream

For further configuration specification, have a look at the example config file incorporating all possible step types and options and take the first character of the options into account:
* `a` = array
* `b` = boolean
* `e` = enum
* `f` = function
* `n` = numeric
* `o` = object
* `s` = string
