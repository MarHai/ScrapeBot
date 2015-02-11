/**
 * ScrapeBot/scrape.js
 *
 * This file runs one config file once.
 * It is meant to be called various times through ScrapeBot/bot.js
 *
 * TOC:
   * initial configuration
   * config interpreter (i.e., the magic)
 *
 * (c) 2015
 * Mario Haim <haim@ifkw.lmu.de>
 * LMU Munich
 */



/***********************
** initial configuration
***********************/

//initial defintions
var oPage = require('casper').create({ verbose: false, logLevel: 'debug' }),
	oFile = require('fs'),
	sCookieFile = '',
	nRunId = new Date(),
	oConfig = {
		uid: null,
		width: 1280,
		height: 720,
		userAgent: 'Mozilla/5.0 (X11; Linux i586; rv:31.0) Gecko/20100101 Firefox/31.0',
		dir: {
			prefix: './',
			config: 'config/',
			cookie: 'cookie/',
			log: 'log/',
			screenshot: 'screenshot/'
		},
		timeout: 800
	};
nRunId = nRunId.getFullYear() + '-' + nRunId.getDate() + '-' + nRunId.getDay() + '_' + 
	nRunId.getHours() + '-' + nRunId.getMinutes() + '-' + nRunId.getSeconds();
function log(_sText) {
	oPage.echo(_sText);
	var dTime = new Date();
	_sText = dTime.toLocaleString() + ' .' + dTime.getMilliseconds() + ' ' + _sText + '\n';
	oFile.write(oConfig.dir.prefix + oConfig.dir.log + oConfig.uid + '.txt', _sText, 'a');
}
function overwriteConfig(_oOption) {
	for(var sKey in _oOption) {
		if(typeof(oConfig[sKey]) !== 'undefined') {
			oConfig[sKey] = _oOption[sKey];
		} else if(sKey.length > 4 && sKey.substr(0, 4) === 'dir.') {
			var sArgument = sKey.substr(4);
			if(typeof(oConfig.dir[sArgument]) !== 'undefined') {
				oConfig.dir[sArgument] = _oOption[sKey];
			}
		}
	}
}



/***********************
** config interpreter
***********************/
overwriteConfig(oPage.cli.options);
if(oConfig.uid === null) {
	//exit with error; no logging due to missing UID
	oPage.echo('ERROR: No uid given');
	oPage.exit();
} else {
	//load config
	var oJson = JSON.parse(oFile.read(oConfig.dir.prefix + oConfig.dir.config + oConfig.uid + '.json')),
		oPublic = require(oConfig.dir.prefix + 'public.js');
	var aStep = oJson.aStep;
	if(typeof(oJson.oConfig) !== 'undefined') {
		overwriteConfig(oJson.oConfig);
	}
	log('Config: ' + JSON.stringify(oConfig));

	//init casper
	phantom.cookiesEnabled = true;
	sCookieFile = oConfig.dir.prefix + oConfig.dir.cookie + oConfig.uid + '.txt';
	if(oFile.exists(sCookieFile)) {
		log('Loading cookies from ' + sCookieFile);
		phantom.cookies = JSON.parse(oFile.read(sCookieFile));
	}
	oPage.start().then(function() {
		this.viewport(oConfig.width, oConfig.height);
		this.userAgent(oConfig.userAgent);
	});
	
	//run through config
	for(var i = 0; i < aStep.length; i++) {
		oPage.then((function(oStep, i) { return function() {
				if(typeof(oStep.eType) === 'undefined') {
					oStep.eType = 'open';
				}
				switch(oStep.eType) {
					case 'click':
						if(typeof(oStep.sSel) === 'undefined') {
							log('ERROR in step ' + i + ': No selector given');
						} else {
							log('[' + i + '] Clicking ' + oStep.sel);
							this.click(oStep.sel);
						}
						break;
						
					case 'eval':
					case 'evaluate':
						if(typeof(oPublic[oStep.fEval]) === 'undefined') {
							log('ERROR in step ' + i + ': No function given');
						} else {
							log('[' + i + '] Evaluating ' + oStep.fEval);
							var aResult = this.evaluate(oPublic[oStep.fEval]),
								dTime = new Date();
							oFile.write(oConfig.dir.prefix + oConfig.dir.log + oConfig.uid + '_eval.json', JSON.stringify({
								dGMT: dTime.toGMTString(),
								nLength: aResult.length,
								aResult: aResult
							}) + '\n', 'a');
						}
						break;
						
					case 'fill':
						if(typeof(oStep.sSel) === 'undefined' || typeof(oStep.oValue) === 'undefined') {
							log('ERROR in step ' + i + ': Form selector or values missing');
						} else {
							if(typeof(oStep.bSubmit) === 'undefined') {
								oStep.bSubmit = false;
							}
							log('[' + i + '] Filling form ' + oStep.sSel + ' (' + JSON.stringify(oStep.oValue) + ')');
							this.fill(oStep.sSel, oStep.oValue, oStep.bSubmit);
						}
						break;
						
					case 'log':
						if(typeof(oStep.sText) !== 'undefined') {
							log(oStep.sText);
						}
						break;
						
					case 'random':
						if(typeof(oStep.aUrl) === 'undefined') {
							log('ERROR in step ' + i + ': No URL array given');
							break;
						} else {
							oStep.sUrl = oStep.aUrl[Math.floor(Math.random() * oStep.aUrl.length)];
						}
						//NO break as we want to continue to open
					case 'open':
						if(typeof(oStep.sUrl) === 'undefined') {
							log('ERROR in step ' + i + ': No URL given');
						} else {
							if(typeof(oStep.oConfig) === 'undefined') {
								oStep.oConfig = {};
							}
							log('[' + i + '] Opening ' + oStep.sUrl);
							this.open(oStep.sUrl, oStep.oConfig);
						}
						break;
						
					case 'reload':
						log('[' + i + '] Reloading page');
						this.reload();
						break;
						
					case 'shot':
					case 'screenshot':
						var sFile = oConfig.uid + '_' + i + '_' + nRunId + '.png';
						log('[' + i + '] Taking screenshot into ' + sFile);
						this.capture(oConfig.dir.prefix + oConfig.dir.screenshot + sFile);
						break;
				}
				this.wait(oConfig.timeout);
			}})(aStep[i], i)
		);
	}
	
	oPage.run(function() {
		log('Storing cookies in ' + sCookieFile);
		oFile.write(sCookieFile, JSON.stringify(phantom.cookies), 664);
		log('Finishing #' + oConfig.uid);
		this.exit();
	});
}
