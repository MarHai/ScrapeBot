module.exports = {
	//extract Google results (main results only, no knowledge graph, no ads, no suggestions)
	extractGoogleResults: function() {
		return [].map.call(__utils__.findAll('h3.r a'), function(_oElem, i) {
			return {
				text: _oElem.innerText,
				link: _oElem.getAttribute('href'),
				preview: _oElem.parentNode.nextSibling.querySelector('span.st').innerText,
				position: ++i
			};
		});
	},
	
	//extract DuckDuckGo results
	extractDuckDuckGoResults: function() {
		return [].map.call(__utils__.findAll('#links h2 > a.result__a'), function(_oElem, i) {
			return {
				text: _oElem.innerText,
				link: _oElem.getAttribute('href'),
				position: ++i
			};
		});
	},
	
	//extract Bing results
	extractBingResults: function() {
		return [].map.call(__utils__.findAll('ol#b_results > li.b_algo h2 a'), function(_oElem, i) {
			return {
				text: _oElem.innerText,
				link: _oElem.getAttribute('href'),
				position: ++i
			};
		});
	},
	
	//extract Tweets
	extractTweets: function() {
		return [].map.call(__utils__.findAll('div.tweet:not(.promoted-tweet) .content'), function(_oElem, i) {
			return {
				text: _oElem.querySelector('.tweet-text').innerText,
				link: _oElem.querySelector('.stream-item-header .time a').getAttribute('href'),
				author: _oElem.querySelector('.stream-item-header > a').getAttribute('href'),
				position: ++i
			};
		});
	},
	
	//extract Google suggestions
	extractGoogleSuggestions: function() {
		return [].map.call(__utils__.findAll('ul.sbsb_b[role="listbox"] > li .sbqs_c'), function(_oElem, i) {
			return {
				text: _oElem.innerText,
				position: ++i
			};
		});
	},
	
	//extract first Google result
	extractFirstGoogleResult: function() {
		var oElem = __utils__.findOne('h3.r a');
		return {
			text: oElem.innerText,
			link: oElem.getAttribute('href'),
			preview: oElem.parentNode.nextSibling.querySelector('span.st').innerText
		};
	}
};
