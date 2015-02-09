# ScrapeBot
ScrapeBot is a CasperJS-based tool in order to visit, modify, and scrape a defined set of webpages regularly. It was built to automate various web-based tasks and keep track of them. Additionally, per configuration, ScrapeBot keeps track of cookies.

## Prerequisites
First, you'll need [CasperJS](http://casperjs.org/). Now, [test it](http://docs.casperjs.org/en/latest/quickstart.html). If up and running, you are ready to go.

## Installation
Clone (or download) the latest version of ScrapeBot:

```
git clone https://github.com/MarHai/ScrapeBot
```

That's it, really. Set up a config file (or use the example one included) and test it:

```
casperjs scrape.js --uid=example
```

## A bit of description
ScrapeBot consists of two major parts:
* **scrape.js** handles all the actions defined within _one config_ file at _one time_
* **bot.js** calls scrape.js with _all available config_ files _regularly_

That means, for starters and in order to test, you just need scrape.js.
For the productive action, you then only need to call bot.js which in turn will handle scrape.js calls.

### scrape.js
Calls look like one of the following:
```
casperjs scrape.js --uid=123
casperjs scrape.js --uid=123 --width=1024
casperjs scrape.js --uid=123 --timeout=1500
casperjs scrape.js --uid=123 --dir.screenshot=img/
```

The `uid` parameter (`123` in these examples) has to match a config file within the specified configuration directory (by default, that is `./config/`). The filename there has to be the specified UID and an additional .json (lower case). In our example, the file has to be `./config/123.json`.

While the `uid` parameter is obligatory, the others are optional. Optional parameters include
* **width** (default: `1280`) and **height** (`720`) indicating the emulated browser's viewport
* **timeout** (default `800`) defining the time waiting after each action (e.g., page load) in milliseconds
* **dir.prefix** (default: `./`) specifies the directory where all other directories are based
* **dir.config** (`config/`), **dir.cookie** (`cookie/`), **dir.log** (`log/`), and **dir.screenshot** (`screenshot/`) are, each, appended to _dir.prefix_ specifying the single directories necessary (note the ending slash)

Please note, that all configuration parameters (except for mandatory uid) may also be specified within each configuration file. The latter overwrites command-line-given parameters.

### bot.js
_to be written_

## Configuration
Each configuration is a JSON file including an `aStep` array of the steps to do and an optional `oConfig` object with the parameters described above (within the _scrape.js_ section). `aStep` needs to have objects as array elements, each representing one step of action. These steps are run through in the given (array) order.

A single step can be one of the following (defined through `eType`, default, if not set, is `open`):

| Type | Description | Options |
|------|-------------|---------|
|eval  |call JavaScript function |`fEval`|
|fill  |fill form (field) |`sSel`, `oValue`, `bSubmit`|
|log   |write into log file |`sText`|
|open  |open URL |`sUrl`|
|reload|reload current page |_none_|
|shot  |screenshot current page |_none_|

For further configuration specification, have a look at the example config file incorporating all possible step types and options and take the first character of the options into account:
* `a` = array
* `b` = boolean
* `e` = enum
* `f` = function
* `n` = numeric
* `o` = object
* `s` = string
